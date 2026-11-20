import argparse
import copy
import datetime
import hashlib
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import yaml

from shortfall import ledger, redact, score
from shortfall.answers import load_causes
from shortfall.budget import CapReached, from_flags
from shortfall.scenario_format import CHECK_NAMES, check_rules_text, format_text
from shortfall.spend import Meter, Usage, now
from shortfall.tools import Snapshot, ToolError

VERSION = "2.22.0"
READ_LINES = 200
RESULT_CHARS = 12_000
RUN_CAP = 300
ATTEMPT_CAP = 30
TURN_CAP = 100
KEEP_TURNS = 6
SHORTEN_EVERY = 6
MODEL_RETRIES = 2
HYPOTHESIS_CHARS = 1_200
CHARS_PER_TOKEN = 3.5
PROMPTS = Path(__file__).resolve().parent / "prompts"

SNAPSHOT_NOTE = (
    f"The snapshot holds only Medusa {VERSION}'s packages/ folder, so every path starts "
    "with packages/. Enterprise Edition files are not available."
)
EXPECTED_CHECKS = (*CHECK_NAMES, "none")
MAX_CLAIMS = 5
VARIANTS = ("v2", "v2-nomenu", "v2-budget", "v2-budget2")
NOMENU = "v2-nomenu"
BUDGET = "v2-budget"
BUDGET2 = "v2-budget2"
GATED = (BUDGET, BUDGET2)
GATE_RUNS = 60
GATE_TEXT = "Finish is not available yet. Keep testing until the run budget is nearly used."
GATE_TEXT2 = (
    "Finish is not available yet. In this mode you never see run results, so don't wait for "
    "them. Submit another attempt until the run budget is nearly used."
)
GATE_TEXTS = {BUDGET: GATE_TEXT, BUDGET2: GATE_TEXT2}
GATE_STOP = 15

TOOLS = [
    {
        "name": "list_files",
        "description": "List the files and folders directly under a folder of the source code. "
        + SNAPSHOT_NOTE,
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Folder, like packages"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": f"Read numbered lines of a source file, at most {READ_LINES} per call. "
        + SNAPSHOT_NOTE,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start": {"type": "integer", "description": "First line, from 1"},
                "end": {"type": "integer", "description": "Last line"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "search",
        "description": "Search the source code for plain text, case-sensitive, at most 50 "
        "matches. " + SNAPSHOT_NOTE,
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "path": {"type": "string", "description": "File or folder to search under"},
            },
            "required": ["text", "path"],
        },
    },
    {
        "name": "submit_attempt",
        "description": "Submit one attempt: the source file you think holds the cause, one "
        "cause id, the one check you expect to fail, a short paragraph with your hypothesis, "
        "and the scenario YAML that tests it.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "One source path, like packages/..."},
                "cause": {"type": "string", "description": "One id from the cause list"},
                "expected_check": {
                    "type": "string",
                    "enum": list(EXPECTED_CHECKS),
                    "description": "The check you expect to fail, or none",
                },
                "hypothesis": {"type": "string", "description": "One short paragraph"},
                "scenario": {"type": "string", "description": "Scenario YAML"},
            },
            "required": ["file", "cause", "expected_check", "hypothesis", "scenario"],
        },
    },
    {
        "name": "finish",
        "description": "End the trial with a short summary and your claims: for each attempt "
        f"you believe found a real problem, its number, the source file and the cause id. "
        f"At most {MAX_CLAIMS} claims, or none.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "claims": {
                    "type": "array",
                    "maxItems": MAX_CLAIMS,
                    "items": {
                        "type": "object",
                        "properties": {
                            "attempt": {"type": "integer", "description": "Attempt number"},
                            "file": {"type": "string", "description": "One source path"},
                            "cause": {"type": "string", "description": "One cause id"},
                        },
                        "required": ["attempt", "file", "cause"],
                    },
                },
            },
            "required": ["summary", "claims"],
        },
    },
]

FEEDBACK = {
    "accepted": "Attempt {number} accepted.",
    "refused": "Attempt {number} refused: {reason}",
    "not_run": "Attempt {number} was not run: the run cap was reached.",
    "left": "Left: {runs} runs, {attempts} attempts, {turns} turns.",
    "left_none": "Left: {attempts} attempts, {turns} turns.",
    "no_runs": "Attempt {number} was recorded but did not run.",
    "head": "Attempt {number} ran {runs} times on Medusa {version}.",
    "check": "{rule} failed in {fail} of {runs}",
    "checks": "Checks: {checks}. Inconclusive runs: {inconclusive}.",
    "runs": "Runs:",
    "run": "{n}. complete calls: {calls}; orders {orders}; {stock}; failed checks: {failed}{note}",
    "call": "{id} {outcome}",
    "level": "{sku} stock {stock_before} to {stock_after}, reserved {reserved_before} to "
    "{reserved_after}",
    "unknown": " (counted inconclusive: a complete call ended with outcome unknown)",
    "harness": " (the run could not be judged)",
    "error": "error: {error}",
    "path_error": "error: {error}. Top-level folders in the snapshot: {folders}",
    "no_tool": "error: no tool named {name!r}",
    "finished": "Trial finished.",
    "finish_refused": "finish refused: {reason}. The trial goes on. Call finish again with "
    "valid claims.",
}


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class Reply:
    tool_calls: tuple[ToolCall, ...] = ()
    text: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    dollars: float = 0.0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    stop_reason: str | None = None


class ModelUnavailable(RuntimeError):
    def __init__(self, message: str, billed: bool = False):
        super().__init__(redact.mask(message))
        self.billed = billed


class RetryLater(RuntimeError):
    def __init__(self, message: str, wait: float):
        super().__init__(redact.mask(message))
        self.wait = wait
        self.billed = False


class Model(Protocol):
    name: str
    sdk_version: str | None
    knowledge_cutoff: str | None

    def max_dollars(self, messages: list[dict], tools: list[dict]) -> float: ...

    def reply(self, messages: list[dict], tools: list[dict]) -> Reply: ...


@dataclass
class ScriptedModel:
    replies: list[Reply]
    name: str = "scripted"
    seen: list[list[dict]] = field(default_factory=list)
    sdk_version: str | None = None
    knowledge_cutoff: str | None = None

    def max_dollars(self, messages: list[dict], tools: list[dict]) -> float:
        return 0.0

    def reply(self, messages: list[dict], tools: list[dict]) -> Reply:
        self.seen.append(json.loads(json.dumps(messages)))
        if len(self.seen) > len(self.replies):
            return Reply(text="The script has no more replies.")
        return self.replies[len(self.seen) - 1]

    @classmethod
    def from_json(cls, items: list[dict], name: str = "scripted") -> "ScriptedModel":
        replies = []
        for n, item in enumerate(items, start=1):
            calls = tuple(
                ToolCall(id=f"call-{n}-{k}", name=c["name"], arguments=c.get("arguments", {}))
                for k, c in enumerate(item.get("tool_calls") or [], start=1)
            )
            replies.append(
                Reply(
                    tool_calls=calls,
                    text=item.get("text"),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                )
            )
        return cls(replies=replies, name=name)


class LeakError(RuntimeError):
    pass


def forbidden_terms(cases_root: Path) -> tuple[str, ...]:
    terms = {"answer.yaml", "benchmark/cases", "benchmark/baselines"}
    for folder in sorted(p for p in Path(cases_root).iterdir() if p.is_dir()):
        terms.add(folder.name)
        for control in score.load_case(folder).controls:
            terms.add(control.file)
            if control.variant:
                terms.add(control.variant)
                terms.update(re.findall(r"[0-9]{4,}", control.variant))
    return tuple(sorted(terms))


def check_leaks(messages: list[dict], terms: tuple[str, ...]) -> None:
    for message in messages:
        text = json.dumps(message, ensure_ascii=False)
        for term in terms:
            if term in text:
                raise LeakError(f"a {message['role']} message holds {term!r}")


def tools_for(variant: str) -> list[dict]:
    if variant not in VARIANTS:
        raise ValueError(f"prompt variant must be one of {', '.join(VARIANTS)}")
    if variant != NOMENU:
        return TOOLS
    tools = copy.deepcopy(TOOLS)
    submit = next(t for t in tools if t["name"] == "submit_attempt")
    submit["description"] = (
        "Submit one attempt: the source file you think holds the cause, the one check you "
        "expect to fail, a short paragraph with your hypothesis, and the scenario YAML that "
        "tests it."
    )
    del submit["parameters"]["properties"]["cause"]
    submit["parameters"]["required"].remove("cause")
    finish = next(t for t in tools if t["name"] == "finish")
    finish["description"] = (
        "End the trial with a short summary and your claims: for each attempt you believe "
        f"found a real problem, its number and the source file. At most {MAX_CLAIMS} claims, "
        "or none."
    )
    items = finish["parameters"]["properties"]["claims"]["items"]
    del items["properties"]["cause"]
    items["required"].remove("cause")
    return tools


def opening(
    root: Path, task_mode: str, issue: str | None, terms: tuple[str, ...], variant: str = "v2"
) -> list[dict]:
    causes = load_causes(root / "benchmark" / "causes.yaml")
    docs = root / ".oversold" / "docs"
    parts = []
    if task_mode == "guided":
        if not issue:
            raise ValueError("guided mode needs an issue")
        parts += [
            (PROMPTS / "guided.md").read_text(encoding="utf-8").strip(),
            "Bug report:\n\n"
            + (root / "snapshots" / "issues" / f"{issue}.md").read_text(encoding="utf-8").strip(),
        ]
    else:
        parts.append((PROMPTS / "unguided.md").read_text(encoding="utf-8").strip())
    parts += [
        (PROMPTS / "setup.md").read_text(encoding="utf-8").strip(),
        "Causes you can name:\n\n" + "\n".join(f"- {k}: {v}" for k, v in causes.items()),
        "Scenario format:\n\n" + format_text(),
        "Check rules:\n\n" + check_rules_text((docs / "checks.md").read_text(encoding="utf-8")),
    ]
    system = "system.md"
    if variant == NOMENU:
        parts = [p for p in parts if not p.startswith("Causes you can name:")]
        system = "system-nomenu.md"
    return [
        {"role": "system", "content": (PROMPTS / system).read_text(encoding="utf-8").strip()},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def enterprise_paths(root: Path) -> tuple[str, ...]:
    path = Path(root) / "benchmark" / "snapshots" / f"enterprise-{VERSION}.json"
    if not path.is_file():
        return ()
    return tuple(json.loads(path.read_text(encoding="utf-8"))["paths"])


def counted_orders(snapshot: dict) -> int:
    return sum(
        1
        for o in snapshot.get("orders") or []
        if not o.get("canceled_at") and o.get("status") != "canceled"
    )


def level_text(sku: str, before: dict, after: dict) -> str:
    return FEEDBACK["level"].format(
        sku=sku,
        stock_before=before.get("stocked_quantity"),
        stock_after=after.get("stocked_quantity"),
        reserved_before=before.get("reserved_quantity"),
        reserved_after=after.get("reserved_quantity"),
    )


def run_summary(n: int, history: dict) -> str:
    calls = ", ".join(
        FEEDBACK["call"].format(id=a["id"], outcome=a.get("outcome") or "not sent")
        for a in (history.get("race") or {}).get("actions") or []
    )
    before = {lv["sku"]: lv for lv in (history.get("before") or {}).get("inventory_levels") or []}
    after = {lv["sku"]: lv for lv in (history.get("after") or {}).get("inventory_levels") or []}
    stock = "; ".join(level_text(sku, before[sku], after.get(sku, {})) for sku in sorted(before))
    failed = [v["check"] for v in history.get("verdicts") or [] if v["result"] == "fail"]
    note = FEEDBACK["unknown"] if score.unknown_completion(history) else ""
    if history.get("harness_error"):
        note = FEEDBACK["harness"]
    return FEEDBACK["run"].format(
        n=n,
        calls=calls or "none",
        orders=counted_orders(history.get("after") or {}),
        stock=stock,
        failed=", ".join(failed) or "none",
        note=note,
    )


def history_feedback(number: int, histories: list[dict]) -> str:
    if not histories:
        return FEEDBACK["no_runs"].format(number=number)
    c = score.counts(histories)
    checks = ", ".join(
        FEEDBACK["check"].format(rule=rule, fail=row["fail"], runs=len(histories))
        for rule, row in c.items()
    )
    lines = [
        FEEDBACK["head"].format(number=number, runs=len(histories), version=VERSION),
        FEEDBACK["checks"].format(checks=checks, inconclusive=score.inconclusive_runs(histories)),
        FEEDBACK["runs"],
    ]
    lines += [run_summary(i, h) for i, h in enumerate(histories, start=1)]
    return "\n".join(lines)


def validate_with_oversold(root: Path, path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["sh", "scripts/oversold.sh", "validate", str(path)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    text = (proc.stdout + proc.stderr).replace(str(path.resolve()), "scenario")
    return proc.returncode == 0, score.clean(text.strip(), root)


@dataclass
class Caps:
    runs: int = RUN_CAP
    attempts: int = ATTEMPT_CAP
    turns: int = TURN_CAP
    dollars: float = 0.0


class Trial:
    def __init__(
        self,
        root: Path,
        model: Model,
        runner: score.Runner,
        *,
        trial_id: str,
        task_mode: str,
        feedback: str,
        issue: str | None = None,
        caps: Caps | None = None,
        image: tuple[str, str] = ("unknown", "none"),
        pin: str = "unknown",
        validate: Callable[[Path, Path], tuple[bool, str]] = validate_with_oversold,
        keep_turns: int = KEEP_TURNS,
        shorten_every: int = SHORTEN_EVERY,
        sleep: Callable[[float], None] = time.sleep,
        variant: str = "v2",
    ):
        if task_mode not in ledger.TASK_MODES:
            raise ValueError(f"task mode must be one of {', '.join(ledger.TASK_MODES)}")
        if feedback not in ledger.FEEDBACK_MODES:
            raise ValueError(f"feedback must be one of {', '.join(ledger.FEEDBACK_MODES)}")
        self.root = Path(root)
        self.model = model
        self.runner = runner
        self.trial_id = trial_id
        self.task_mode = task_mode
        self.feedback = feedback
        self.issue = issue
        self.caps = caps or Caps()
        self.image = image
        self.pin = pin
        self.validate = validate
        self.keep_turns = keep_turns
        self.shorten_every = shorten_every
        self.sleep = sleep
        self.variant = variant
        self.tools = tools_for(variant)
        self.ledger_path = score.ledger_path_for(self.root)
        self.folder = self.root / "runs" / "agent" / trial_id
        self.folder.mkdir(parents=True, exist_ok=False)
        self.transcript = self.folder / "transcript.jsonl"
        self.cases = score.load_cases(self.root / "benchmark" / "cases")
        self.causes = load_causes(self.root / "benchmark" / "causes.yaml")
        self.terms = forbidden_terms(self.root / "benchmark" / "cases")
        self.snapshot = Snapshot(
            self.root / "snapshots" / f"medusa-{VERSION}",
            READ_LINES,
            RESULT_CHARS,
            enterprise_paths(self.root),
        )
        before = ledger.spent(ledger.load(self.ledger_path))["dollars"]
        self.budget = from_flags(self.caps.runs, self.caps.dollars or None, before)
        self.meter = Meter(self.ledger_path, self.budget, f"{trial_id}-model")
        self.messages = opening(self.root, task_mode, issue, self.terms, variant)
        self.turns = 0
        self.attempts = 0
        self.tokens = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
        self.end: str | None = None
        self.notes: dict[str, tuple[int, str]] = {}
        self.claims: list[dict] | None = None
        self.gate_answers = 0
        self.gate_turns: set[int] = set()
        self.folders = ", ".join(
            sorted(f"{p.name}/" for p in self.snapshot.root.iterdir() if p.is_dir())
        )

    def log(self, event: dict) -> None:
        with self.transcript.open("a", encoding="utf-8") as f:
            f.write(redact.mask(json.dumps(event, ensure_ascii=False)) + "\n")

    def shortening_turn(self, completed: int) -> bool:
        return completed > 0 and completed % self.shorten_every == 0

    def shorten(self) -> None:
        if not self.shortening_turn(self.turns):
            return
        for message in self.messages:
            if message["role"] != "tool":
                continue
            turn, note = self.notes[message["tool_call_id"]]
            if self.turns - turn >= self.keep_turns and message["content"] != note:
                message["content"] = note

    def stable_end(self) -> int:
        coming = self.turns + 1
        if not self.shortening_turn(coming):
            return len(self.messages)
        for i, message in enumerate(self.messages):
            if message["role"] != "tool":
                continue
            turn, note = self.notes[message["tool_call_id"]]
            if coming - turn >= self.keep_turns and message["content"] != note:
                return i
        return len(self.messages)

    def model_view(self) -> list[dict]:
        view = [dict(m) for m in self.messages]
        view[self.stable_end() - 1]["cache"] = True
        return view

    def tool_result(self, call: ToolCall, content: str, note: str) -> None:
        removed = f"[{note}: removed after {self.keep_turns} or more turns]"
        self.notes[call.id] = (self.turns, removed)
        self.messages.append(
            {"role": "tool", "tool_call_id": call.id, "name": call.name, "content": content}
        )
        self.log({"event": "tool", "turn": self.turns, "call": call.id, "content": content})

    def run(self) -> dict:
        ledger.append(
            self.ledger_path,
            {
                "kind": "agent-trial",
                "attempt_id": f"{self.trial_id}-trial",
                "source": "agent",
                "trial_id": self.trial_id,
                "task_mode": self.task_mode,
                "feedback": self.feedback,
                "issue": self.issue,
                "model": self.model.name,
                "prompts": self.variant,
                "sdk_version": getattr(self.model, "sdk_version", None),
                "knowledge_cutoff": getattr(self.model, "knowledge_cutoff", None),
                "medusa_version": VERSION,
                "run_cap": self.caps.runs,
                "attempt_cap": self.caps.attempts,
                "turn_cap": self.caps.turns,
                "dollar_cap": self.caps.dollars,
                "oversold_commit": self.pin,
                "timestamp": now(),
            },
        )
        self.log({"event": "opening", "messages": self.messages})
        while self.end is None:
            if self.counted_turns() >= self.caps.turns:
                self.end = f"turn cap: {self.caps.turns} turns"
                break
            self.shorten()
            try:
                check_leaks(self.messages, self.terms)
                reply = self.call_model()
            except CapReached as err:
                self.end = f"dollar cap: {err}"
                break
            except LeakError as err:
                self.end = f"leak guard: {err}"
                break
            except ModelUnavailable as err:
                self.end = f"model API stopped the trial: {err}"
                break
            self.turns += 1
            self.tokens["input"] += reply.input_tokens
            self.tokens["cache_write"] += reply.cache_write_tokens
            self.tokens["cache_read"] += reply.cache_read_tokens
            self.tokens["output"] += reply.output_tokens
            self.messages.append(
                {
                    "role": "assistant",
                    "content": reply.text or "",
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in reply.tool_calls
                    ],
                }
            )
            self.log(
                {
                    "event": "reply",
                    "turn": self.turns,
                    "message": self.messages[-1],
                    "stop_reason": reply.stop_reason,
                    "input_tokens": reply.input_tokens,
                    "cache_write_tokens": reply.cache_write_tokens,
                    "cache_read_tokens": reply.cache_read_tokens,
                    "output_tokens": reply.output_tokens,
                    "dollars": reply.dollars,
                }
            )
            if not reply.tool_calls and self.gated():
                if not reply.text:
                    self.messages.pop()
                self.messages.append({"role": "user", "content": GATE_TEXTS[self.variant]})
                self.gate("no tool call")
                continue
            if not reply.tool_calls:
                self.end = "the model stopped without calling finish"
                if reply.stop_reason not in (None, "end_turn", "tool_use"):
                    self.end += f" (stop reason {reply.stop_reason})"
                break
            for call in reply.tool_calls:
                self.handle(call)
                if self.end:
                    break
        spent = ledger.spent(
            [r for r in ledger.load(self.ledger_path) if r["attempt_id"].startswith(self.trial_id)]
        )
        summary = {
            "kind": "agent-end",
            "attempt_id": f"{self.trial_id}-end",
            "source": "agent",
            "trial_id": self.trial_id,
            "reason": self.end,
            "turns": self.turns,
            "attempts": self.attempts,
            "oversold_runs": spent["oversold_runs"],
            "dollars": spent["dollars"],
            "input_tokens": self.tokens["input"],
            "cache_write_tokens": self.tokens["cache_write"],
            "cache_read_tokens": self.tokens["cache_read"],
            "output_tokens": self.tokens["output"],
            "claims": self.claims,
            "timestamp": now(),
        }
        if self.variant in GATED:
            summary["gate_answers"] = self.gate_answers
        ledger.append(self.ledger_path, summary)
        self.log({"event": "end", **summary})
        return summary

    def call_model(self) -> Reply:
        view = self.model_view()

        def call():
            reply = self.model.reply(view, self.tools)
            usage = Usage(
                self.model.name,
                reply.input_tokens,
                reply.output_tokens,
                reply.dollars,
                reply.cache_write_tokens,
                reply.cache_read_tokens,
            )
            return reply, usage

        for retry in range(MODEL_RETRIES + 1):
            try:
                cap = self.model.max_dollars(view, self.tools)
                return self.meter.paid_call(self.model.name, cap, call)
            except RetryLater as err:
                if retry == MODEL_RETRIES:
                    raise ModelUnavailable(f"{err}, still failing after {retry} retries") from None
                self.log({"event": "retry", "turn": self.turns + 1, "error": str(err)})
                self.sleep(err.wait)
        raise AssertionError("unreachable")

    def counted_turns(self) -> int:
        if self.variant == BUDGET2:
            return self.turns - len(self.gate_turns)
        return self.turns

    def gated(self) -> bool:
        return (
            self.variant in GATED
            and self.budget.session_left() > GATE_RUNS
            and self.attempts < self.caps.attempts
            and self.counted_turns() < self.caps.turns
        )

    def gate(self, kind: str) -> None:
        self.gate_answers += 1
        self.gate_turns.add(self.turns)
        text = GATE_TEXTS[self.variant]
        self.log({"event": "gate", "turn": self.turns, "kind": kind, "content": text})
        if self.variant == BUDGET2 and self.gate_answers >= GATE_STOP:
            self.end = f"stopped after {GATE_STOP} gate answers"

    def left(self) -> str:
        key = "left_none" if self.feedback == "none" else "left"
        return FEEDBACK[key].format(
            runs=self.budget.session_left(),
            attempts=max(self.caps.attempts - self.attempts, 0),
            turns=max(self.caps.turns - self.counted_turns(), 0),
        )

    def check_claims(self, value) -> tuple[list[dict], str | None]:
        if not isinstance(value, list):
            return [], "claims must be a list, empty if you claim nothing"
        if len(value) > MAX_CLAIMS:
            return [], f"at most {MAX_CLAIMS} claims"
        out = []
        for n, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                return [], f"claim {n} must have attempt, file and cause"
            attempt, file, cause = item.get("attempt"), item.get("file"), item.get("cause")
            if type(attempt) is not int or not 1 <= attempt <= self.attempts:
                return [], (
                    f"claim {n}: attempt must be the number of an attempt you submitted, "
                    f"1 to {self.attempts}"
                    if self.attempts
                    else f"claim {n}: you have not submitted any attempt"
                )
            if not (isinstance(file, str) and file.startswith("packages/")):
                return [], f"claim {n}: file must be one source path under packages/"
            if self.safe(file) != file:
                return [], f"claim {n}: file must not hold a local path"
            if self.variant == NOMENU:
                out.append({"attempt": attempt, "file": file})
                continue
            if cause not in self.causes:
                return [], f"claim {n}: cause must be one id from the cause list"
            out.append({"attempt": attempt, "file": file, "cause": cause})
        return out, None

    def handle(self, call: ToolCall) -> None:
        args = call.arguments if isinstance(call.arguments, dict) else {}
        try:
            if call.name == "list_files":
                path = args.get("path", ".")
                self.tool_result(call, self.snapshot.list_files(path), f"list_files {path}")
            elif call.name == "read_file":
                path = args.get("path")
                start, end = args.get("start", 1), args.get("end")
                text = self.snapshot.read_file(path, start, end)
                self.tool_result(call, text, f"read_file {path} from line {start}")
            elif call.name == "search":
                text, path = args.get("text"), args.get("path", ".")
                result = self.snapshot.search(text, path)
                self.tool_result(call, result, f"search {text!r} under {path}")
            elif call.name == "submit_attempt":
                text = self.submit(args) + "\n" + self.left()
                self.tool_result(call, text, f"submit_attempt {self.attempts}")
                if self.end is None and self.attempts >= self.caps.attempts:
                    self.end = f"attempt cap: {self.caps.attempts} attempts"
            elif call.name == "finish" and self.gated():
                self.tool_result(call, GATE_TEXTS[self.variant], "finish not available")
                self.gate("finish")
            elif call.name == "finish":
                claims, reason = self.check_claims(args.get("claims"))
                if reason:
                    text = FEEDBACK["finish_refused"].format(reason=reason)
                    self.tool_result(call, text, "finish refused")
                    self.log({"event": "finish-refused", "reason": reason})
                else:
                    self.claims = claims
                    self.tool_result(call, FEEDBACK["finished"], "finish")
                    self.end = "finished by the model"
                    self.log({"event": "finish", "summary": args.get("summary"), "claims": claims})
            else:
                self.tool_result(call, FEEDBACK["no_tool"].format(name=call.name), call.name)
        except ToolError as err:
            if call.name in ("list_files", "read_file", "search"):
                text = FEEDBACK["path_error"].format(error=err, folders=self.folders)
            else:
                text = FEEDBACK["error"].format(error=err)
            self.tool_result(call, text, f"{call.name} error")

    def safe(self, value) -> str:
        text = str(value)
        return "(withheld: looks like a local path)" if ledger.looks_local(text) else text

    def refuse(self, number: int, args: dict, reason: str) -> str:
        ledger.append(
            self.ledger_path,
            {
                "kind": "prediction",
                "attempt_id": f"{self.trial_id}-{number:02d}",
                "source": "agent",
                "trial_id": self.trial_id,
                "attempt": number,
                "file": self.safe(args.get("file")),
                "cause": None if self.variant == NOMENU else self.safe(args.get("cause")),
                "hypothesis": self.safe(args.get("hypothesis")),
                "scenario_sha256": None,
                "expected_check": None
                if args.get("expected_check") is None
                else self.safe(args.get("expected_check")),
                "refused": reason,
                "timestamp": now(),
            },
        )
        return FEEDBACK["refused"].format(number=number, reason=reason)

    def submit(self, args: dict) -> str:
        self.attempts += 1
        number = self.attempts
        file, cause = args.get("file"), args.get("cause")
        if self.variant == NOMENU:
            cause = None
        hypothesis, text = args.get("hypothesis"), args.get("scenario")
        if not (isinstance(file, str) and file.startswith("packages/")):
            return self.refuse(number, args, "file must be one source path under packages/")
        if self.variant != NOMENU and cause not in self.causes:
            return self.refuse(number, args, "cause must be one id from the cause list")
        expected = args.get("expected_check")
        if expected not in EXPECTED_CHECKS:
            return self.refuse(
                number, args, "expected_check must be one of the five check names, or none"
            )
        if not (isinstance(hypothesis, str) and hypothesis.strip()):
            return self.refuse(number, args, "hypothesis must be a short paragraph")
        if self.safe(hypothesis) != hypothesis or self.safe(file) != file:
            return self.refuse(number, args, "file and hypothesis must not hold a local path")
        if len(hypothesis) > HYPOTHESIS_CHARS or "\n\n" in hypothesis.strip():
            return self.refuse(
                number,
                args,
                f"hypothesis must be one paragraph of at most {HYPOTHESIS_CHARS} characters",
            )
        try:
            data = yaml.safe_load(text) if isinstance(text, str) else None
            score.check_candidate(data)
        except (yaml.YAMLError, score.CandidateRefused) as err:
            reason = (
                str(err)
                if isinstance(err, score.CandidateRefused)
                else "scenario is not valid YAML"
            )
            return self.refuse(number, args, reason)
        submitted = self.folder / f"submitted-{number:02d}.yaml"
        submitted.write_text(text, encoding="utf-8")
        ok, message = self.validate(self.root, submitted)
        if not ok:
            return self.refuse(number, args, f"oversold validate: {message}")
        data["target"]["version"] = VERSION
        data["name"] = f"attempt-{number:02d}-{self.trial_id.lower()}"
        scenario = self.folder / f"attempt-{number:02d}.yaml"
        scenario_text = yaml.safe_dump(data, sort_keys=False, default_flow_style=False, width=80)
        scenario.write_text(scenario_text, encoding="utf-8")
        if self.budget.session_left() < score.SCREEN_RUNS:
            self.end = f"run cap: {self.caps.runs} runs"
            return FEEDBACK["not_run"].format(number=number)
        attempt_id = f"{self.trial_id}-{number:02d}"
        ledger.append(
            self.ledger_path,
            {
                "kind": "prediction",
                "attempt_id": attempt_id,
                "source": "agent",
                "trial_id": self.trial_id,
                "attempt": number,
                "file": file,
                "cause": cause,
                "hypothesis": hypothesis,
                "scenario_sha256": hashlib.sha256(scenario_text.encode()).hexdigest(),
                "expected_check": expected,
                "refused": None,
                "timestamp": now(),
            },
        )
        meta = {"attempt_id": attempt_id, "source": "agent", "seed": 0, "rerun_of": None}

        def factory():
            return score.Attempt(
                self.root,
                scenario,
                VERSION,
                self.runner,
                self.budget,
                self.cases,
                self.image[0],
                self.image[1],
                self.pin,
                meta,
                self.ledger_path,
                named_file=file,
                named_cause=cause,
            )

        attempts, stop = score.run_attempts([factory], self.budget, report=lambda line: None)
        histories = []
        if attempts:
            a = attempts[0]
            histories = a.histories["screen"] + a.histories["retry"] + a.histories["score"]
        if stop:
            self.end = (
                f"run cap: {self.caps.runs} runs"
                if "session runs cap" in stop
                else f"stopped: {stop}"
            )
        if self.feedback == "none":
            return FEEDBACK["accepted"].format(number=number)
        return history_feedback(number, histories)


def estimate(
    opening_chars: int,
    read_chars: int,
    feedback_chars: int,
    call_chars: int,
    submit_chars: int,
    attempts: int = ATTEMPT_CAP,
    turns: int = TURN_CAP,
    keep: int = KEEP_TURNS,
) -> dict:
    reads_per_attempt = max(turns // attempts - 1, 0)
    history: list[tuple[int, int]] = []
    input_chars = output_chars = 0
    for turn in range(turns):
        context = opening_chars + sum(
            out + (res if turn - t < keep else 80) for t, (out, res) in enumerate(history)
        )
        input_chars += context
        submitting = (turn + 1) % (reads_per_attempt + 1) == 0
        out = submit_chars if submitting else call_chars
        res = feedback_chars if submitting else read_chars
        output_chars += out
        history.append((out, res))
    return {
        "turns": turns,
        "attempts": attempts,
        "input_tokens": round(input_chars / CHARS_PER_TOKEN),
        "output_tokens": round(output_chars / CHARS_PER_TOKEN),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.agent")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one trial")
    who = run.add_mutually_exclusive_group(required=True)
    who.add_argument("--script", help="JSON list of scripted replies")
    who.add_argument("--model", help="Claude model id, like claude-haiku-5-5")
    run.add_argument("--task-mode", choices=ledger.TASK_MODES, required=True)
    run.add_argument("--issue", help="case whose issue the guided mode shows")
    run.add_argument("--feedback", choices=ledger.FEEDBACK_MODES, required=True)
    run.add_argument("--max-runs", type=int, default=RUN_CAP)
    run.add_argument("--max-attempts", type=int, default=ATTEMPT_CAP)
    run.add_argument("--max-turns", type=int, default=TURN_CAP)
    run.add_argument("--raise-dollar-cap", type=float, default=0.0)
    est = sub.add_parser("estimate", help="estimate tokens for one trial")
    est.add_argument("--issue", default="medusa-16502-lines")
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "estimate":
        print(json.dumps(estimate_trial(root, args.issue), indent=2))
        return 0
    if args.script:
        model = ScriptedModel.from_json(json.loads(Path(args.script).read_text(encoding="utf-8")))
    else:
        from shortfall.models import AnthropicModel

        model = AnthropicModel(args.model, env_path=root / ".env")
    runner = score.OversoldRunner(root)
    image = runner.image(VERSION)
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    trial = Trial(
        root,
        model,
        runner,
        trial_id=f"agent-{stamp}",
        task_mode=args.task_mode,
        feedback=args.feedback,
        issue=args.issue,
        caps=Caps(
            runs=args.max_runs,
            attempts=args.max_attempts,
            turns=args.max_turns,
            dollars=args.raise_dollar_cap,
        ),
        image=image,
        pin=runner.pin,
    )
    print(json.dumps(trial.run(), indent=2))
    return 0


def estimate_trial(root: Path, issue: str) -> dict:
    terms = forbidden_terms(root / "benchmark" / "cases")
    opening_chars = len(json.dumps(opening(root, "guided", issue, terms)))
    opening_chars += len(json.dumps(TOOLS))
    manifest = json.loads((root / "benchmark" / "snapshots" / f"medusa-{VERSION}.json").read_text())
    read_chars = min(manifest["ts_files"]["p90_chars"], RESULT_CHARS)
    feedback_chars = 20 * 260
    out = estimate(
        opening_chars=opening_chars,
        read_chars=read_chars,
        feedback_chars=feedback_chars,
        call_chars=200,
        submit_chars=2_000,
    )
    out["assumed_chars"] = {
        "opening_with_tools": opening_chars,
        "file_read": read_chars,
        "history_feedback": feedback_chars,
        "tool_call": 200,
        "submit_call": 2_000,
        "chars_per_token": CHARS_PER_TOKEN,
    }
    return out


if __name__ == "__main__":
    sys.exit(main())
