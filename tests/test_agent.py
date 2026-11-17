import copy
import json
import re
import shutil
from pathlib import Path

import pytest

from shortfall import agent, ledger, score, sweep
from shortfall.agent import Caps, Reply, ScriptedModel, ToolCall, Trial

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"
PLAIN = json.loads((DATA / "histories" / "five-checks-fail.json").read_text(encoding="utf-8"))
MARK = 777
SCENARIO = sweep.to_yaml(sweep.grid(0)[0])
CASE_IDS = sorted(p.name for p in (ROOT / "benchmark" / "cases").iterdir() if p.is_dir())
RESULT_WORDS = (
    "reproduced",
    "not isolated",
    "cut off",
    "located",
    "not accepted",
    "control",
    "scoring",
    "fix build",
    str(MARK),
)


def control_history() -> dict:
    h = copy.deepcopy(PLAIN)
    for v in h["verdicts"]:
        v["result"] = "pass"
    for snap in (h["before"], h["after"]):
        for level in snap["inventory_levels"]:
            level["stocked_quantity"] = MARK
    return h


class FakeRunner:
    def __init__(self, plain=None, ledger_path=None):
        self.plain = plain or PLAIN
        self.calls: list[tuple[str, int]] = []
        self.ledger_path = ledger_path
        self.seen_predictions: list[list[str]] = []

    def run(self, scenario: Path, runs: int, version: str) -> score.RunSet:
        self.calls.append((scenario.stem, runs))
        if self.ledger_path:
            self.seen_predictions.append(
                [
                    r["attempt_id"]
                    for r in ledger.load(self.ledger_path)
                    if r["kind"] == "prediction"
                ]
            )
        source = control_history() if scenario.stem.endswith("-control") else self.plain
        return score.RunSet(
            folder=f"runs/fake-{len(self.calls)}",
            histories=[copy.deepcopy(source) for _ in range(runs)],
        )


def make_root(tmp_path: Path) -> Path:
    shutil.copytree(
        ROOT / "benchmark" / "cases",
        tmp_path / "benchmark" / "cases",
        ignore=shutil.ignore_patterns("results"),
    )
    shutil.copy(ROOT / "benchmark" / "causes.yaml", tmp_path / "benchmark" / "causes.yaml")
    docs = tmp_path / ".oversold" / "docs"
    docs.mkdir(parents=True)
    (docs / "scenario-format.md").write_text(
        "# Scenario format\n\n"
        "./bin/oversold run x.yaml --version 2.22.0 --variant pr-16961\n"
        "| Field | Type |\n|---|---|\n"
        "| `target.servers` | integer |\n"
        "| `target.variant` | string |\n"
        "| `target.locking` | string |\n"
        "Seeded stock: WIDGET 10, SOLO 1.\n",
        encoding="utf-8",
    )
    (docs / "checks.md").write_text("# Checks\n\nno_oversell: never promise more units.\n")
    shutil.copytree(DATA / "snapshot", tmp_path / "snapshots" / "medusa-2.22.0")
    issues = tmp_path / "snapshots" / "issues"
    issues.mkdir()
    for case_id in CASE_IDS:
        (issues / f"{case_id}.md").write_text(
            "# Two carts sell the last unit\n\nIssue: https://github.com/medusajs/medusa/issues/"
            f"{case_id.split('-')[1]}\n"
            "\nTwo buyers complete at the same moment.\n",
            encoding="utf-8",
        )
    return tmp_path


@pytest.fixture
def root(tmp_path):
    return make_root(tmp_path)


def call(name: str, **arguments) -> ToolCall:
    call.n = getattr(call, "n", 0) + 1
    return ToolCall(id=f"c{call.n}", name=name, arguments=arguments)


def reply(*calls: ToolCall, text: str | None = None) -> Reply:
    return Reply(tool_calls=calls, text=text, input_tokens=1000, output_tokens=100)


def submit(scenario: str = SCENARIO, cause: str = "process-local-lock") -> ToolCall:
    return call(
        "submit_attempt",
        file="packages/core/src/cart.ts",
        cause=cause,
        expected_check="no_oversell",
        hypothesis="Two servers each reserve the last unit, so both orders go through.",
        scenario=scenario,
    )


def trial(root, replies, feedback="history", task_mode="unguided", caps=None, runner=None, **kw):
    model = ScriptedModel(replies=list(replies))
    runner = runner or FakeRunner(ledger_path=score.ledger_path_for(root))
    t = Trial(
        root,
        model,
        runner,
        trial_id=kw.pop("trial_id", "agent-t1"),
        task_mode=task_mode,
        feedback=feedback,
        issue="medusa-17032-last-unit" if task_mode == "guided" else None,
        caps=caps,
        image=("sha256:" + "1" * 64, "none"),
        pin="a" * 40,
        validate=kw.pop("validate", lambda r, p: (True, "valid")),
        **kw,
    )
    return t, model, runner


def results(model: ScriptedModel) -> list[str]:
    final = model.seen[-1]
    return [m["content"] for m in final if m["role"] == "tool"]


REFUSED = SCENARIO.replace("  servers: 2\n", "  servers: 2\n  locking: redis\n")


def full_script():
    return [
        reply(call("list_files", path="packages")),
        reply(call("read_file", path="packages/core/src/cart.ts")),
        reply(call("search", text="reserveInventory", path="packages")),
        reply(submit(REFUSED)),
        reply(submit()),
        reply(call("finish", summary="done", claims=[])),
    ]


@pytest.mark.parametrize("feedback", ["none", "history"])
def test_a_scripted_trial_end_to_end(root, feedback):
    t, model, runner = trial(root, full_script(), feedback=feedback)
    end = t.run()
    assert end["reason"] == "finished by the model"
    assert (end["turns"], end["attempts"]) == (6, 2)
    out = results(model)
    assert out[0].startswith("packages: 2 folders, 1 files")
    assert out[1].startswith("packages/core/src/cart.ts, lines 1 to 5 of 5")
    assert "reserveInventory" in out[2]
    assert out[3] == (
        "Attempt 1 refused: a candidate may not set target.locking, only the harness sets them\n"
        "Left: 300 runs, 11 attempts, 56 turns."
    )
    assert out[4].endswith("\nLeft: 267 runs, 10 attempts, 55 turns.")
    if feedback == "none":
        assert out[4] == "Attempt 2 accepted.\nLeft: 267 runs, 10 attempts, 55 turns."
    else:
        assert out[4].startswith("Attempt 2 ran 13 times on Medusa 2.22.0.")
        assert "no_oversell failed in 13 of 13" in out[4]
        assert "no_missing_orders failed in 0 of 13" in out[4]
        assert "1. complete calls: complete-a ok, complete-b ok; orders 2;" in out[4]
        assert "WIDGET stock 10 to 10" in out[4]
        assert len([line for line in out[4].splitlines() if re.match(r"[0-9]+\. ", line)]) == 13
    assert [c for c, _ in runner.calls if c.endswith("-control")] == [
        "attempt-02-pr-16961-control",
        "attempt-02-pr-17420-control",
    ]
    records = ledger.load(score.ledger_path_for(root))
    kinds = [r["kind"] for r in records]
    assert kinds[0] == "agent-trial" and kinds[-1] == "agent-end"
    preds = [r for r in records if r["kind"] == "prediction"]
    assert [(p["attempt"], p["refused"] is None) for p in preds] == [(1, False), (2, True)]
    assert [p["expected_check"] for p in preds] == ["no_oversell", "no_oversell"]
    assert records[-1]["claims"] == []
    final = next(r for r in records if r["kind"] == "final")
    assert final["source"] == "agent"
    assert final["violation"]["result"] == "violation"
    assert final["reproduced"]["cases"]["medusa-17032-last-unit"] == "reproduced"
    assert final["located"]["file"] == "packages/core/src/cart.ts"
    assert final["located"]["cause"] == "process-local-lock"
    model_spend = [r for r in records if r["attempt_id"] == "agent-t1-model"]
    assert [r["state"] for r in model_spend] == ["reserved", "settled"] * 6
    assert {(r["model"], r["input_tokens"], r["output_tokens"]) for r in model_spend[1::2]} == {
        ("scripted", 1000, 100)
    }
    assert end["input_tokens"] == 6000 and end["output_tokens"] == 600
    assert (t.folder / "transcript.jsonl").exists()
    scenario = (t.folder / "attempt-02.yaml").read_text()
    assert "name: attempt-02-agent-t1" in scenario and "version: 2.22.0" in scenario


def test_the_prediction_is_in_the_ledger_before_the_first_run(root):
    t, model, runner = trial(root, full_script())
    t.run()
    assert runner.seen_predictions[0] == ["agent-t1-01", "agent-t1-02"]


def test_a_scenario_that_fails_validate_is_refused_and_costs_no_runs(root):
    def bad(r, p):
        return False, "scenario: invalid: carts: at least one cart"

    t, model, runner = trial(
        root, [reply(submit()), reply(call("finish", summary="x", claims=[]))], validate=bad
    )
    t.run()
    assert results(model)[0].splitlines()[0] == (
        "Attempt 1 refused: oversold validate: scenario: invalid: carts: at least one cart"
    )
    assert runner.calls == []
    assert t.attempts == 1


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"scenario": SCENARIO + "checks: [no_oversell]\n"}, "may not set checks"),
        (
            {"scenario": SCENARIO.replace("servers: 2\n", "servers: 2\n  variant: x\n", 1)},
            "target.variant",
        ),
        ({"scenario": "carts: [\n"}, "not valid YAML"),
        ({"cause": "race-condition"}, "cause must be one id"),
        ({"file": "/etc/passwd"}, "file must be one source path"),
        ({"hypothesis": "a\n\nb"}, "one paragraph"),
        ({"expected_check": "no_double_sale"}, "expected_check must be one of"),
        ({"scenario": SCENARIO + "notes: hi\n"}, "may not set notes: not a field"),
    ],
)
def test_bad_submissions_are_refused(root, change, reason):
    args = {
        "file": "packages/core/src/cart.ts",
        "cause": "per-line-check",
        "expected_check": "none",
        "hypothesis": "short",
        "scenario": SCENARIO,
        **change,
    }
    t, model, runner = trial(
        root,
        [
            reply(ToolCall("s", "submit_attempt", args)),
            reply(call("finish", summary="x", claims=[])),
        ],
    )
    t.run()
    assert reason in results(model)[0]
    assert runner.calls == []


def test_the_turn_cap_ends_the_trial(root):
    reads = [reply(call("list_files", path="packages")) for _ in range(5)]
    t, _, _ = trial(root, reads, caps=Caps(turns=3))
    assert t.run()["reason"] == "turn cap: 3 turns"
    assert t.turns == 3


def test_the_attempt_cap_ends_the_trial(root):
    t, model, runner = trial(
        root, [reply(submit(REFUSED)), reply(submit(REFUSED))], caps=Caps(attempts=2)
    )
    assert t.run()["reason"] == "attempt cap: 2 attempts"
    assert t.turns == 2


def test_the_run_cap_ends_the_trial(root):
    t, model, runner = trial(root, [reply(submit()), reply(submit())], caps=Caps(runs=20))
    end = t.run()
    assert end["reason"] == "run cap: 20 runs"
    assert end["oversold_runs"] <= 20
    assert t.turns == 1


def test_no_attempt_starts_without_room_for_a_screen(root):
    t, model, runner = trial(root, [reply(submit())], caps=Caps(runs=2))
    assert t.run()["reason"] == "run cap: 2 runs"
    assert runner.calls == []


class Paid(ScriptedModel):
    def max_dollars(self, messages, tools):
        return 0.4


def test_the_dollar_cap_ends_the_trial(root):
    replies = [
        Reply(
            tool_calls=(call("list_files", path="packages"),),
            input_tokens=10,
            output_tokens=5,
            dollars=0.3,
        )
        for _ in range(5)
    ]
    model = Paid(replies=replies, name="paid-test")
    t = Trial(
        root,
        model,
        FakeRunner(),
        trial_id="agent-t9",
        task_mode="unguided",
        feedback="none",
        caps=Caps(dollars=1.0),
        validate=lambda r, p: (True, ""),
    )
    end = t.run()
    assert end["reason"].startswith("dollar cap: session dollars cap reached")
    assert t.turns == 3
    assert end["dollars"] == pytest.approx(0.9)
    spend = [r for r in ledger.load(score.ledger_path_for(root)) if r["kind"] == "spend"]
    assert [r["state"] for r in spend] == ["reserved", "settled"] * 3


def test_old_tool_results_are_shortened(root):
    replies = [reply(call("read_file", path="packages/core/src/cart.ts")) for _ in range(9)]
    replies.append(reply(call("finish", summary="x", claims=[])))
    t, model, _ = trial(root, replies)
    t.run()
    last = [m["content"] for m in model.seen[-1] if m["role"] == "tool"]
    assert len(last) == 9
    assert (
        last[:3] == ["[read_file packages/core/src/cart.ts from line 1: removed after 6 turns]"] * 3
    )
    assert all(m.startswith("packages/core/src/cart.ts, lines 1 to 5") for m in last[3:])
    full = [
        json.loads(line)
        for line in (t.folder / "transcript.jsonl").read_text().splitlines()
        if json.loads(line)["event"] == "tool"
    ]
    assert all(e["content"].startswith("packages/core/src/cart.ts") for e in full[:-1])


def test_read_file_gives_at_most_200_lines_and_cuts_at_12000_characters(root):
    big = root / "snapshots" / "medusa-2.22.0" / "packages" / "big.ts"
    big.write_text("".join(f"line {n} " + "x" * 100 + "\n" for n in range(1, 500)))
    t, model, _ = trial(
        root,
        [
            reply(call("read_file", path="packages/big.ts")),
            reply(call("finish", summary="x", claims=[])),
        ],
    )
    t.run()
    out = results(model)[0]
    assert len(out) == agent.RESULT_CHARS
    assert out.endswith("characters]")
    small = root / "snapshots" / "medusa-2.22.0" / "packages" / "small.ts"
    small.write_text("".join(f"{n}\n" for n in range(1, 500)))
    t, model, _ = trial(
        root,
        [
            reply(call("read_file", path="packages/small.ts")),
            reply(call("finish", summary="x", claims=[])),
        ],
        trial_id="agent-t2",
    )
    t.run()
    assert results(model)[0].splitlines()[0] == "packages/small.ts, lines 1 to 200 of 499"


@pytest.mark.parametrize("task_mode", ["guided", "unguided"])
@pytest.mark.parametrize("feedback", ["none", "history"])
def test_nothing_forbidden_reaches_the_model(root, task_mode, feedback):
    t, model, _ = trial(root, full_script(), feedback=feedback, task_mode=task_mode)
    assert t.run()["reason"] == "finished by the model"
    terms = agent.forbidden_terms(root / "benchmark" / "cases")
    for term in ("pr-16961", "pr-17420", "16961", "17420", "answer.yaml", *CASE_IDS):
        assert term in terms
    seen = json.dumps(model.seen)
    for term in (*terms, *RESULT_WORDS):
        assert term not in seen, term
    assert "Two buyers complete at the same moment." in seen if task_mode == "guided" else True
    assert ("Bug report" in seen) == (task_mode == "guided")
    assert "| `OVS-SOLO` | `SOLO` | 1 | 1 |" in seen
    assert "\\nchecks:" not in seen and "`checks`" not in seen
    assert "target.servers" in seen and "target.locking" not in json.dumps(model.seen[0])


def test_the_leak_guard_ends_a_trial(root):
    leaky = root / "snapshots" / "medusa-2.22.0" / "packages" / "notes.ts"
    leaky.write_text("see pr-17420 for the fix\n")
    t, model, _ = trial(
        root,
        [
            reply(call("read_file", path="packages/notes.ts")),
            reply(call("finish", summary="x", claims=[])),
        ],
    )
    end = t.run()
    assert end["reason"].startswith("leak guard: a tool message holds")
    assert "17420" in end["reason"]
    assert len(model.seen) == 1


def test_scripted_model_from_json():
    model = ScriptedModel.from_json(
        [{"tool_calls": [{"name": "finish", "arguments": {"summary": "x"}}], "input_tokens": 5}]
    )
    r = model.reply([], [])
    assert r.tool_calls[0].name == "finish" and r.input_tokens == 5
    assert model.reply([], []).text == "The script has no more replies."


def test_the_token_estimate(capsys):
    est = agent.estimate(
        opening_chars=34_000,
        read_chars=6_677,
        feedback_chars=5_200,
        call_chars=200,
        submit_chars=2_000,
    )
    assert (est["turns"], est["attempts"]) == (60, 12)
    shorter = agent.estimate(34_000, 6_677, 5_200, 200, 2_000, keep=60)
    assert est["input_tokens"] < shorter["input_tokens"]
    assert est["output_tokens"] == round((48 * 200 + 12 * 2_000) / 3.5)
    print(json.dumps(est))


@pytest.mark.skipif(
    not (ROOT / ".oversold" / "docs" / "checks.md").exists(),
    reason="needs the pinned Oversold clone",
)
def test_the_estimate_for_the_real_prompt(capsys):
    est = agent.estimate_trial(ROOT, "medusa-16502-lines")
    assert est["assumed_chars"]["opening_with_tools"] > 20_000
    print(json.dumps(est))


def test_env_example_has_only_the_key_name():
    assert (ROOT / ".env.example").read_text() == "ANTHROPIC_API_KEY=\n"


def test_a_bad_path_shows_the_top_level_folders(root):
    t, model, _ = trial(
        root,
        [
            reply(call("read_file", path="src/index.ts")),
            reply(call("finish", summary="x", claims=[])),
        ],
    )
    t.run()
    assert results(model)[0] == (
        "error: src/index.ts: not found. Top-level folders in the snapshot: packages/"
    )


def test_tool_descriptions_name_the_snapshot():
    for tool in agent.TOOLS[:3]:
        assert "only Medusa 2.22.0's packages/ folder" in tool["description"]


def test_claims_are_checked_before_finish_takes_effect(root):
    replies = full_script()[:-1] + [
        reply(
            call(
                "finish",
                summary="x",
                claims=[{"attempt": 3, "file": "packages/a.ts", "cause": "per-line-check"}],
            )
        ),
        reply(
            call(
                "finish",
                summary="x",
                claims=[{"attempt": 2, "file": "packages/a.ts", "cause": "bad"}],
            )
        ),
        reply(call("finish", summary="x")),
        reply(call("finish", summary="x", claims=[{}] * 6)),
        reply(
            call(
                "finish",
                summary="found it",
                claims=[
                    {"attempt": 2, "file": "packages/core/src/cart.ts", "cause": "per-line-check"},
                    {"attempt": 1, "file": "packages/core/src/cart.ts", "cause": "per-line-check"},
                ],
            )
        ),
    ]
    t, model, _ = trial(root, replies)
    end = t.run()
    assert end["reason"] == "finished by the model"
    assert end["turns"] == 10
    out = results(model)
    assert out[5].startswith("finish refused: claim 1: attempt must be the number of an attempt")
    assert "claim 1: cause must be one id" in out[6]
    assert "claims must be a list" in out[7]
    assert "at most 5 claims" in out[8]
    assert all(o.endswith("Call finish again with valid claims.") for o in out[5:9])
    records = ledger.load(score.ledger_path_for(root))
    assert records[-1]["claims"] == [
        {"attempt": 2, "file": "packages/core/src/cart.ts", "cause": "per-line-check"},
        {"attempt": 1, "file": "packages/core/src/cart.ts", "cause": "per-line-check"},
    ]


def test_a_trial_without_finish_has_no_claims(root):
    t, _, _ = trial(root, [reply(call("list_files", path="packages"))], caps=Caps(turns=1))
    end = t.run()
    assert end["reason"] == "turn cap: 1 turns"
    assert ledger.load(score.ledger_path_for(root))[-1]["claims"] is None
