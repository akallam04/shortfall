import argparse
import copy
import datetime
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import anthropic

from shortfall import ledger, redact, score
from shortfall.agent import (
    TOOLS,
    ModelUnavailable,
    Reply,
    RetryLater,
    ToolCall,
    forbidden_terms,
    opening,
)
from shortfall.budget import from_flags
from shortfall.spend import Meter, Usage

API_URL = "https://api.anthropic.com"
MAX_TOKENS = 2_000
TIMEOUT_SECONDS = 120.0
RESERVE_MARGIN = 0.05
RESERVE_EXTRA_TOKENS = 512
RETRY_WAIT = 5.0
MAX_WAIT = 60.0
EPHEMERAL = {"type": "ephemeral"}
KEY_NAME = "ANTHROPIC_API_KEY"
BILLING_WORDS = ("credit balance", "billing", "spend limit", "spend cap", "payment")
BILLING_ERRORS = (anthropic.EnforcedSpendLimitReachedError, anthropic.OrganizationOnHoldError)

PRICES_CHECKED = "2026-11-17"
PRICES_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
CUTOFF_SOURCE = "https://platform.claude.com/docs/en/models/overview"


@dataclass(frozen=True)
class Price:
    input: float
    cache_write: float
    cache_read: float
    output: float


@dataclass(frozen=True)
class ModelSpec:
    tiers: tuple[tuple[int | None, Price], ...]
    knowledge_cutoff: str
    thinking: dict


MODELS = {
    "claude-haiku-5-5": ModelSpec(
        tiers=(
            (100_000, Price(input=0.10, cache_write=0.125, cache_read=0.01, output=0.50)),
            (None, Price(input=0.50, cache_write=0.625, cache_read=0.05, output=2.50)),
        ),
        knowledge_cutoff="Jun 2026",
        thinking={"type": "disabled"},
    ),
    "claude-sonnet-5-5": ModelSpec(
        tiers=((None, Price(input=2.00, cache_write=2.50, cache_read=0.10, output=10.00)),),
        knowledge_cutoff="Jun 2026",
        thinking={"type": "between_tools"},
    ),
}


class KeyMissing(RuntimeError):
    pass


def load_key(path: Path) -> str:
    path = Path(path)
    if not path.is_file():
        raise KeyMissing(f"{path.name} not found: put {KEY_NAME}=<key> in it")
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip().removeprefix("export ").strip()
        if not text.startswith(f"{KEY_NAME}="):
            continue
        value = text.split("=", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            redact.register(value)
            return value
    raise KeyMissing(f"{path.name} has no {KEY_NAME} line with a value")


def price_for(spec: ModelSpec, prompt_tokens: int) -> Price:
    for limit, price in spec.tiers:
        if limit is None or prompt_tokens <= limit:
            return price
    raise ValueError("no price tier")


def dollars(
    spec: ModelSpec, input_tokens: int, cache_write: int, cache_read: int, output_tokens: int
) -> float:
    p = price_for(spec, input_tokens + cache_write + cache_read)
    total = (
        input_tokens * p.input
        + cache_write * p.cache_write
        + cache_read * p.cache_read
        + output_tokens * p.output
    )
    return total / 1_000_000


def reservation(spec: ModelSpec, counted_tokens: int, max_tokens: int) -> float:
    bound = math.ceil(counted_tokens * (1 + RESERVE_MARGIN)) + RESERVE_EXTRA_TOKENS
    p = price_for(spec, bound)
    return (bound * max(p.input, p.cache_write) + max_tokens * p.output) / 1_000_000


def error_wait(err: anthropic.APIStatusError) -> float:
    try:
        value = float(err.response.headers.get("retry-after", ""))
    except (TypeError, ValueError):
        return RETRY_WAIT
    return min(max(value, 1.0), MAX_WAIT)


def classify(err: anthropic.APIStatusError) -> Exception:
    status = err.status_code
    text = redact.mask(str(err.message))[:300]
    billing = (
        status == 402
        or isinstance(err, BILLING_ERRORS)
        or any(word in text.lower() for word in BILLING_WORDS)
    )
    if status == 401:
        return ModelUnavailable(f"authentication error ({status}): {text}")
    if status == 403:
        return ModelUnavailable(f"permission error ({status}): {text}")
    if billing:
        return ModelUnavailable(f"billing error ({status}): {text}")
    if status == 429:
        return RetryLater(f"rate limited ({status}): {text}", error_wait(err))
    if status >= 500:
        return RetryLater(f"server error ({status}): {text}", error_wait(err))
    return ModelUnavailable(f"API error ({status}): {text}")


def guarded(call):
    try:
        return call()
    except anthropic.APIStatusError as err:
        raise classify(err) from None
    except anthropic.APIConnectionError as err:
        raise ModelUnavailable(
            f"could not reach the model API ({type(err).__name__})", billed=True
        ) from None


def api_tools(tools: list[dict]) -> list[dict]:
    out = [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]
    out[-1]["cache_control"] = dict(EPHEMERAL)
    return out


def rebuilt_blocks(message: dict) -> list[dict]:
    blocks = []
    if message.get("content"):
        blocks.append({"type": "text", "text": message["content"]})
    for c in message.get("tool_calls") or []:
        blocks.append(
            {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]}
        )
    return blocks


class AnthropicModel:
    def __init__(
        self,
        model_id: str,
        *,
        client=None,
        env_path: Path | None = None,
        max_tokens: int = MAX_TOKENS,
    ):
        if model_id not in MODELS:
            raise ValueError(f"no prices for {model_id}, known: {', '.join(sorted(MODELS))}")
        self.name = model_id
        self.spec = MODELS[model_id]
        self.sdk_version = anthropic.__version__
        self.knowledge_cutoff = self.spec.knowledge_cutoff
        self.max_tokens = max_tokens
        if client is None:
            if env_path is None:
                raise ValueError("give a client or the path of the .env file")
            client = anthropic.Anthropic(
                api_key=load_key(env_path),
                base_url=API_URL,
                max_retries=0,
                timeout=TIMEOUT_SECONDS,
            )
        self.client = client
        self.blocks: dict[str, list[dict]] = {}
        self.counted: int | None = None

    def convert(self, messages: list[dict]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            if role == "user":
                out.append({"role": "user", "content": [{"type": "text", "text": m["content"]}]})
            elif role == "assistant":
                ids = [c["id"] for c in m.get("tool_calls") or []]
                kept = self.blocks.get(ids[0]) if ids else None
                blocks = copy.deepcopy(kept) if kept else rebuilt_blocks(m)
                out.append({"role": "assistant", "content": blocks})
            elif role == "tool":
                block = {
                    "type": "tool_result",
                    "tool_use_id": m["tool_call_id"],
                    "content": m["content"],
                }
                last = out[-1] if out else None
                if last and last["role"] == "user" and last["content"][-1]["type"] == "tool_result":
                    last["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            if m.get("cache") and out:
                out[-1]["content"][-1]["cache_control"] = dict(EPHEMERAL)
        return out

    def request(self, messages: list[dict], tools: list[dict]) -> dict:
        system = next(m["content"] for m in messages if m["role"] == "system")
        return {
            "model": self.name,
            "max_tokens": self.max_tokens,
            "system": [{"type": "text", "text": system, "cache_control": dict(EPHEMERAL)}],
            "tools": api_tools(tools),
            "messages": self.convert(messages),
            "thinking": dict(self.spec.thinking),
        }

    def max_dollars(self, messages: list[dict], tools: list[dict]) -> float:
        params = self.request(messages, tools)
        params.pop("max_tokens")
        counted = guarded(lambda: self.client.messages.count_tokens(**params))
        self.counted = int(counted.input_tokens)
        return reservation(self.spec, self.counted, self.max_tokens)

    def reply(self, messages: list[dict], tools: list[dict]) -> Reply:
        params = self.request(messages, tools)
        response = guarded(lambda: self.client.messages.create(**params))
        calls: list[ToolCall] = []
        texts: list[str] = []
        kept: list[dict] = []
        for block in response.content:
            if block.type == "text":
                if block.text:
                    texts.append(block.text)
                    kept.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                args = block.input if isinstance(block.input, dict) else {}
                calls.append(ToolCall(id=block.id, name=block.name, arguments=args))
                kept.append(
                    {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                )
            elif block.type == "thinking":
                kept.append(
                    {"type": "thinking", "thinking": block.thinking, "signature": block.signature}
                )
            elif block.type == "redacted_thinking":
                kept.append({"type": "redacted_thinking", "data": block.data})
        if calls:
            self.blocks[calls[0].id] = kept
        usage = response.usage
        counts = (
            int(usage.input_tokens or 0),
            int(usage.cache_creation_input_tokens or 0),
            int(usage.cache_read_input_tokens or 0),
            int(usage.output_tokens or 0),
        )
        return Reply(
            tool_calls=tuple(calls),
            text="\n".join(texts) or None,
            input_tokens=counts[0],
            output_tokens=counts[3],
            dollars=dollars(self.spec, *counts),
            cache_write_tokens=counts[1],
            cache_read_tokens=counts[2],
            stop_reason=response.stop_reason,
        )


def smoke(root: Path, model: AnthropicModel, dollar_cap: float, line: str, calls: int = 2):
    ledger_path = score.ledger_path_for(root)
    before = ledger.spent(ledger.load(ledger_path))["dollars"]
    meter = Meter(ledger_path, from_flags(0, dollar_cap, before), f"{smoke_id()}-model")
    system = opening(root, "unguided", None, forbidden_terms(root / "benchmark" / "cases"))[0]
    messages = [system, {"role": "user", "content": line}]
    out = []
    for _ in range(calls):
        cap = model.max_dollars(messages, TOOLS)

        def call():
            r = model.reply(messages, TOOLS)
            u = Usage(
                model.name,
                r.input_tokens,
                r.output_tokens,
                r.dollars,
                r.cache_write_tokens,
                r.cache_read_tokens,
            )
            return r, u

        r = meter.paid_call(model.name, cap, call)
        out.append(
            {
                "counted_input_tokens": model.counted,
                "reserved_dollars": round(cap, 8),
                "input_tokens": r.input_tokens,
                "cache_write_tokens": r.cache_write_tokens,
                "cache_read_tokens": r.cache_read_tokens,
                "output_tokens": r.output_tokens,
                "dollars": round(r.dollars, 8),
                "stop_reason": r.stop_reason,
            }
        )
    return out


def smoke_id() -> str:
    return "smoke-" + datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.models")
    sub = p.add_subparsers(dest="command", required=True)
    sm = sub.add_parser("smoke", help="two identical small calls to check usage and caching")
    sm.add_argument("--model", required=True)
    sm.add_argument("--raise-dollar-cap", type=float, required=True)
    sm.add_argument("--max-tokens", type=int, default=50)
    sm.add_argument("--line", default="In one short sentence, which tool would you call first?")
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    model = AnthropicModel(args.model, env_path=root / ".env", max_tokens=args.max_tokens)
    result = smoke(root, model, args.raise_dollar_cap, args.line)
    print(
        json.dumps(
            {"model": model.name, "sdk_version": model.sdk_version, "calls": result}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
