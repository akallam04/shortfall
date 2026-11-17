import copy
import json
import math
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from test_agent import SCENARIO, FakeRunner, make_root

from shortfall import ledger, redact, score
from shortfall.agent import TOOLS, Caps, Trial
from shortfall.models import (
    MODELS,
    PRICES_CHECKED,
    PRICES_SOURCE,
    RETRY_WAIT,
    AnthropicModel,
    KeyMissing,
    dollars,
    load_key,
    reservation,
)

HAIKU = MODELS["claude-haiku-5-5"]
SONNET = MODELS["claude-sonnet-5-5"]
FAKE_KEY = "sk-ant-api03-" + "Zz9" * 12


def usage(i=1000, w=0, r=0, o=100):
    return SimpleNamespace(
        input_tokens=i, cache_creation_input_tokens=w, cache_read_input_tokens=r, output_tokens=o
    )


def tool_use(n: int, name: str, **args):
    return SimpleNamespace(type="tool_use", id=f"toolu_{n:03d}", name=name, input=args)


def response(*blocks, u=None, stop="tool_use"):
    return SimpleNamespace(content=list(blocks), usage=u or usage(), stop_reason=stop)


def status_error(cls, status: int, message: str = "error", headers: dict | None = None):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx2.Response(status, request=request, headers=headers or {})
    return cls(message, response=resp, body={"type": "error", "error": {"message": message}})


class FakeMessages:
    def __init__(self, replies, count=10_000, errors=()):
        self.replies = list(replies)
        self.count = count
        self.errors = list(errors)
        self.created: list[dict] = []
        self.counted: list[dict] = []

    def count_tokens(self, **kw):
        self.counted.append(copy.deepcopy(kw))
        return SimpleNamespace(input_tokens=self.count)

    def create(self, **kw):
        self.created.append(copy.deepcopy(kw))
        if self.errors:
            err = self.errors.pop(0)
            if err is not None:
                raise err
        return self.replies.pop(0)


class FakeClient:
    def __init__(self, replies, **kw):
        self.messages = FakeMessages(replies, **kw)


@pytest.fixture
def root(tmp_path):
    return make_root(tmp_path)


def model_trial(root, replies, caps=None, keep_turns=6, model_id="claude-haiku-5-5", **kw):
    client = FakeClient(replies, **kw)
    model = AnthropicModel(model_id, client=client)
    sleeps: list[float] = []
    t = Trial(
        root,
        model,
        FakeRunner(ledger_path=score.ledger_path_for(root)),
        trial_id="agent-m1",
        task_mode="unguided",
        feedback="history",
        caps=caps or Caps(dollars=0.5),
        image=("sha256:" + "1" * 64, "none"),
        pin="a" * 40,
        validate=lambda r, p: (True, "valid"),
        keep_turns=keep_turns,
        sleep=sleeps.append,
    )
    return t, client, sleeps


def finish(n: int = 99):
    return response(tool_use(n, "finish", summary="done"), stop="tool_use")


def lines(root, kind=None):
    records = ledger.load(score.ledger_path_for(root))
    return [r for r in records if kind is None or r.get("kind") == kind]


def strip_cache(value):
    if isinstance(value, dict):
        return {k: strip_cache(v) for k, v in value.items() if k != "cache_control"}
    if isinstance(value, list):
        return [strip_cache(v) for v in value]
    return value


def marker(messages: list[dict]) -> tuple[int, int]:
    found = [
        (i, j)
        for i, m in enumerate(messages)
        for j, b in enumerate(m["content"])
        if "cache_control" in b
    ]
    assert len(found) == 1
    return found[0]


def test_prices_are_dated_and_sourced():
    assert PRICES_CHECKED == "2026-11-17"
    assert PRICES_SOURCE == "https://platform.claude.com/docs/en/about-claude/pricing"


def test_usage_to_dollars_for_both_haiku_tiers_and_sonnet():
    assert dollars(HAIKU, 50_000, 30_000, 20_000, 1_000) == pytest.approx(0.00945)
    assert dollars(HAIKU, 50_001, 30_000, 20_000, 1_000) == pytest.approx(0.0472505)
    assert dollars(SONNET, 1_000, 2_000, 3_000, 400) == pytest.approx(0.0113)


@pytest.mark.parametrize("counted", [1_000, 40_000, 95_000, 99_999, 150_000])
@pytest.mark.parametrize("spec", [HAIKU, SONNET])
def test_the_reservation_covers_the_most_a_call_can_cost(spec, counted):
    r = reservation(spec, counted, 2_000)
    for prompt in (counted, math.floor(counted * 1.05) + 512):
        for split in ((prompt, 0, 0), (0, prompt, 0), (0, 0, prompt)):
            assert r >= dollars(spec, *split, 2_000) - 1e-12


def test_the_reservation_uses_the_price_for_its_prompt_size():
    low = reservation(HAIKU, 90_000, 2_000)
    high = reservation(HAIKU, 96_000, 2_000)
    assert low == pytest.approx(((90_000 * 1.05 + 512) * 0.125 + 2_000 * 0.50) / 1e6)
    assert high == pytest.approx(((96_000 * 1.05 + 512) * 0.625 + 2_000 * 2.50) / 1e6)


def test_usage_is_recorded_per_call_with_four_counts(root):
    replies = [
        response(tool_use(1, "list_files", path="packages"), u=usage(400, 8_000, 0, 50)),
        response(tool_use(2, "finish", summary="x"), u=usage(300, 200, 8_000, 40)),
    ]
    t, client, _ = model_trial(root, replies)
    end = t.run()
    assert end["reason"] == "finished by the model"
    settled = [r for r in lines(root, "spend") if r["state"] == "settled"]
    assert [
        (r["input_tokens"], r["cache_write_tokens"], r["cache_read_tokens"], r["output_tokens"])
        for r in settled
    ] == [(400, 8_000, 0, 50), (300, 200, 8_000, 40)]
    assert settled[0]["dollars"] == pytest.approx(dollars(HAIKU, 400, 8_000, 0, 50))
    reserved = [r for r in lines(root, "spend") if r["state"] == "reserved"]
    assert all(r["dollars"] == pytest.approx(reservation(HAIKU, 10_000, 2_000)) for r in reserved)
    assert (end["input_tokens"], end["cache_write_tokens"]) == (700, 8_200)
    assert (end["cache_read_tokens"], end["output_tokens"]) == (8_000, 90)


def test_the_trial_line_names_model_sdk_and_cutoff(root):
    t, _, _ = model_trial(root, [finish()])
    t.run()
    (line,) = lines(root, "agent-trial")
    assert line["model"] == "claude-haiku-5-5"
    assert line["sdk_version"] == anthropic.__version__
    assert line["knowledge_cutoff"] == "Jun 2026"


def test_the_request_shape(root):
    t, client, _ = model_trial(root, [finish()])
    t.run()
    (req,) = client.messages.created
    assert req["model"] == "claude-haiku-5-5"
    assert req["max_tokens"] == 2_000
    assert req["thinking"] == {"type": "disabled"}
    assert not {"temperature", "top_p", "top_k"} & set(req)
    assert [x["name"] for x in req["tools"]] == [x["name"] for x in TOOLS]
    assert req["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert all("cache_control" not in x for x in req["tools"][:-1])
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert marker(req["messages"]) == (0, 0)
    counted = client.messages.counted[0]
    assert "max_tokens" not in counted and counted["messages"] == req["messages"]


def test_sonnet_uses_its_lowest_thinking_setting(root):
    t, client, _ = model_trial(root, [finish()], model_id="claude-sonnet-5-5")
    t.run()
    assert client.messages.created[0]["thinking"] == {"type": "between_tools"}


def test_tool_results_go_back_together_after_the_assistant_turn(root):
    replies = [
        response(tool_use(1, "list_files", path="packages"), tool_use(2, "list_files", path=".")),
        finish(),
    ]
    t, client, _ = model_trial(root, replies)
    t.run()
    second = client.messages.created[1]["messages"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    assert [b["type"] for b in second[1]["content"]] == ["tool_use", "tool_use"]
    assert [b["tool_use_id"] for b in second[2]["content"]] == ["toolu_001", "toolu_002"]


def test_the_cache_marker_moves_to_the_last_message_the_next_turn_keeps(root):
    reads = [
        response(tool_use(n, "read_file", path="packages/core/src/cart.ts"), u=usage())
        for n in range(1, 10)
    ]
    t, client, _ = model_trial(root, [*reads, finish()], keep_turns=3)
    t.run()
    created = client.messages.created
    assert len(created) == 10
    assert any(
        b.get("content", "").startswith("[read_file")
        for m in created[-1]["messages"]
        for b in m["content"]
        if b["type"] == "tool_result"
    )
    for before, after in zip(created, created[1:], strict=False):
        assert sum("cache_control" in json.dumps(x) for x in before["tools"]) == 1
        i, j = marker(before["messages"])
        old = strip_cache(before["messages"])
        new = strip_cache(after["messages"])
        assert new[:i] == old[:i]
        assert new[i]["content"][: j + 1] == old[i]["content"][: j + 1]
    early = [marker(c["messages"])[0] for c in created[:3]]
    assert early == [len(c["messages"]) - 1 for c in created[:3]]
    late = created[-1]["messages"]
    assert marker(late)[0] < len(late) - 1


def test_a_call_over_the_trial_dollar_cap_is_not_made(root):
    t, client, _ = model_trial(root, [finish()], caps=Caps(dollars=0.0001))
    end = t.run()
    assert end["reason"].startswith("dollar cap: session dollars cap reached")
    assert client.messages.created == []
    assert lines(root, "spend") == []


def test_a_call_over_the_total_cap_is_not_made(root):
    ledger.append(
        score.ledger_path_for(root),
        {
            "kind": "spend",
            "attempt_id": "earlier-model",
            "spend_id": "earlier-model-s01",
            "item": "paid_call",
            "state": "settled",
            "set": None,
            "oversold_runs": None,
            "model": "claude-haiku-5-5",
            "input_tokens": 1,
            "output_tokens": 1,
            "dollars": 19.999,
            "timestamp": "2026-11-17T00:00:00+00:00",
        },
    )
    t, client, _ = model_trial(root, [finish()], caps=Caps(dollars=0.5))
    end = t.run()
    assert end["reason"].startswith("dollar cap: total dollars cap reached")
    assert client.messages.created == []


def test_retries_reserve_again_and_wait(root):
    errors = [
        status_error(anthropic.InternalServerError, 529, "Overloaded"),
        status_error(anthropic.RateLimitError, 429, "rate limited", {"retry-after": "3"}),
        None,
    ]
    t, client, sleeps = model_trial(root, [finish()], errors=errors)
    end = t.run()
    assert end["reason"] == "finished by the model"
    assert len(client.messages.created) == 3
    assert sleeps == [RETRY_WAIT, 3.0]
    spends = lines(root, "spend")
    assert [r["state"] for r in spends] == ["reserved", "settled"] * 3
    assert [r["dollars"] for r in spends if r["state"] == "settled"][:2] == [0, 0]
    assert ledger.spent(lines(root))["unsettled_calls"] == 0


def test_a_third_failure_ends_the_trial(root):
    errors = [status_error(anthropic.InternalServerError, 500, "boom") for _ in range(3)]
    t, client, sleeps = model_trial(root, [finish()], errors=errors)
    end = t.run()
    assert end["reason"] == (
        "model API stopped the trial: server error (500): boom, still failing after 2 retries"
    )
    assert len(client.messages.created) == 3
    assert len(sleeps) == 2


@pytest.mark.parametrize(
    "err, start",
    [
        (status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"), "authentication"),
        (status_error(anthropic.PermissionDeniedError, 403, "no access"), "permission"),
        (status_error(anthropic.APIStatusError, 402, "payment required"), "billing"),
        (
            status_error(anthropic.BadRequestError, 400, "Your credit balance is too low"),
            "billing",
        ),
        (status_error(anthropic.RateLimitError, 429, "monthly spend cap reached"), "billing"),
    ],
)
def test_billing_and_auth_errors_end_the_trial_at_once(root, err, start):
    t, client, sleeps = model_trial(root, [finish()], errors=[err])
    end = t.run()
    assert end["reason"].startswith(f"model API stopped the trial: {start} error")
    assert len(client.messages.created) == 1
    assert sleeps == []
    assert end["attempts"] == 0
    assert ledger.spent(lines(root))["dollars"] == 0
    assert ledger.spent(lines(root))["unsettled_calls"] == 0


def test_an_unreachable_api_keeps_the_reservation(root):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.APIConnectionError(request=request)
    t, _, _ = model_trial(root, [finish()], errors=[err])
    end = t.run()
    assert end["reason"].startswith("model API stopped the trial: could not reach")
    assert ledger.spent(lines(root))["unsettled_calls"] == 1
    reserved = reservation(HAIKU, 10_000, 2_000)
    assert ledger.spent(lines(root))["dollars"] == pytest.approx(reserved, abs=1e-6)


def test_load_key_reads_only_the_named_line(tmp_path):
    env = tmp_path / ".env"
    with pytest.raises(KeyMissing) as missing:
        load_key(env)
    assert str(tmp_path) not in str(missing.value)
    env.write_text("OTHER=1\n", encoding="utf-8")
    with pytest.raises(KeyMissing):
        load_key(env)
    env.write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")
    with pytest.raises(KeyMissing):
        load_key(env)
    env.write_text(f'OTHER=1\nANTHROPIC_API_KEY="{FAKE_KEY}"\n', encoding="utf-8")
    assert load_key(env) == FAKE_KEY
    assert FAKE_KEY not in redact.mask(f"error with {FAKE_KEY}")


def test_the_ledger_writer_masks_keys(tmp_path):
    redact.register("plain-registered-secret-42")
    path = tmp_path / "ledger.jsonl"
    ledger.append(
        path,
        {
            "kind": "prediction",
            "attempt_id": "agent-k1-01",
            "source": "agent",
            "trial_id": "agent-k1",
            "attempt": 1,
            "file": "packages/core/src/cart.ts",
            "cause": "process-local-lock",
            "hypothesis": f"uses {FAKE_KEY} and sk-ant-admin01-abcdefghijklmnop and "
            "plain-registered-secret-42 and ANTHROPIC_API_KEY=whatever123",
            "scenario_sha256": "0" * 64,
            "refused": None,
            "timestamp": "2026-11-17T00:00:00+00:00",
        },
    )
    text = path.read_text(encoding="utf-8")
    for secret in (FAKE_KEY, "sk-ant-admin01", "plain-registered-secret-42", "whatever123"):
        assert secret not in text
    assert text.count(redact.MASK) == 4
    assert ledger.load(path)[0]["kind"] == "prediction"


def test_the_transcript_writer_masks_keys(root):
    replies = [
        response(
            SimpleNamespace(type="text", text=f"my key is {FAKE_KEY}"),
            tool_use(1, "search", text=FAKE_KEY, path="packages"),
        ),
        finish(),
    ]
    t, _, _ = model_trial(root, replies)
    t.run()
    text = t.transcript.read_text(encoding="utf-8")
    assert FAKE_KEY not in text
    assert redact.MASK in text
    assert FAKE_KEY not in score.ledger_path_for(root).read_text(encoding="utf-8")


def test_a_submitted_attempt_runs_through_the_client(root):
    replies = [
        response(
            tool_use(
                1,
                "submit_attempt",
                file="packages/core/src/cart.ts",
                cause="process-local-lock",
                hypothesis="Two servers each reserve the last unit.",
                scenario=SCENARIO,
            )
        ),
        finish(),
    ]
    t, client, _ = model_trial(root, replies)
    end = t.run()
    assert end["attempts"] == 1 and end["oversold_runs"] > 0
    feedback = client.messages.created[1]["messages"][-1]["content"][0]["content"]
    assert feedback.startswith("Attempt 1 ran")


def test_an_unknown_model_is_refused():
    with pytest.raises(ValueError):
        AnthropicModel("claude-unknown", client=FakeClient([]))


def test_the_client_ignores_base_url_and_token_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9/elsewhere")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-from-the-shell-not-dotenv")
    env = tmp_path / ".env"
    env.write_text(f"ANTHROPIC_API_KEY={FAKE_KEY}\n", encoding="utf-8")
    model = AnthropicModel("claude-haiku-5-5", env_path=env)
    assert str(model.client.base_url).rstrip("/") == "https://api.anthropic.com"
    assert model.client.api_key == FAKE_KEY
    assert model.client.max_retries == 0
