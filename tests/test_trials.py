import gzip
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from test_agent import SCENARIO, FakeRunner, call, full_script, make_root, reply, trial

from shortfall import freeze, launch, ledger, score, trials
from shortfall.agent import ModelUnavailable, Reply, ScriptedModel
from shortfall.trialscore import score_trial

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "sha256:" + "1" * 64


class Oversold(FakeRunner):
    pin = "a" * 40

    def image(self, version):
        return IMAGE, "none"


def script() -> list[Reply]:
    return [
        reply(
            call(
                "submit_attempt",
                file="packages/core/src/cart.ts",
                cause="process-local-lock",
                expected_check="no_oversell",
                hypothesis="Two servers each reserve the last unit.",
                scenario=SCENARIO,
            )
        ),
        reply(
            call(
                "finish",
                summary="done",
                claims=[
                    {"attempt": 1, "file": "packages/core/src/cart.ts", "cause": "per-line-check"}
                ],
            )
        ),
    ]


@pytest.fixture
def root(tmp_path):
    root = make_root(tmp_path)
    shutil.copy(ROOT / "oversold.lock", root / "oversold.lock")
    (root / freeze.HASH_FILE).parent.mkdir(parents=True)
    (root / freeze.HASH_FILE).write_text(freeze.hash_file_text(root))
    nomenu = root / freeze.HASH_FILES["v2-nomenu"]
    nomenu.write_text(freeze.hash_file_text(root, "v2-nomenu"))
    return root


def write_plan(root: Path, **over) -> Path:
    pin = (root / "oversold.lock").read_text().split("commit=")[1].strip()
    data = {
        "schema": trials.PLAN_SCHEMA,
        "name": "test-plan",
        "model": "scripted",
        "script": "runs/script.json",
        "mode": "guided",
        "cells": [{"issue": 17032, "feedback": "none"}, {"issue": 17032, "feedback": "history"}],
        "trials_per_cell": 1,
        "caps": {"runs": 300, "attempts": 12, "turns": 60, "dollars": 1},
        "dollar_cap": 3,
        "prompt_hash": freeze.prompt_hash(root),
        "oversold_pin": pin,
        "images": {"2.22.0": IMAGE, "2.22.0-pr-17420": IMAGE},
        "order": "round-robin",
        "export_root": "benchmark/export",
        **over,
    }
    path = root / "plan.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def make_runner(root, plan_path, cap=3.0, model=None, **kw):
    plan = trials.load_plan(root, plan_path)
    checks = trials.Checks(
        engine_name=lambda: "colima-shortfall",
        image_id=lambda version, variant: IMAGE,
        vm_free_bytes=lambda: 10**12,
        mac_free_bytes=lambda r: 10**12,
        oversold_running=lambda: False,
        postgres_answers=lambda port: True,
    )

    def exporter(folder, dest):
        dest.mkdir(parents=True)
        (dest / "report.json").write_text("{}")

    return trials.Runner(
        root,
        plan,
        cap,
        make_model=model or (lambda: ScriptedModel(replies=script())),
        runner=Oversold(ledger_path=score.ledger_path_for(root)),
        checks=kw.pop("checks", checks),
        exporter=exporter,
        verifier=lambda folder: (True, ""),
        scanner=kw.pop("scanner", lambda folder: []),
        validate=lambda r, p: (True, "valid"),
    )


def events(root):
    return trials.State(root, trials.load_plan(root, root / "plan.yaml")).events()


def kinds(root):
    return [e["event"] for e in events(root)]


def test_round_robin_order(root):
    cells = [{"issue": 16502, "feedback": "none"}, {"issue": 17032, "feedback": "history"}]
    plan = trials.load_plan(root, write_plan(root, cells=cells, trials_per_cell=3))
    assert [s.id for s in trials.trial_order(plan)] == [
        "16502-none-1",
        "17032-history-1",
        "16502-none-2",
        "17032-history-2",
        "16502-none-3",
        "17032-history-3",
    ]


def test_a_plan_runs_exports_and_skips_finished_trials(root):
    path = write_plan(root)
    assert make_runner(root, path).run() == 0
    for trial_id in ("17032-none-1", "17032-history-1"):
        dest = root / "benchmark" / "export" / trial_id
        names = {p.name for p in dest.iterdir()}
        assert {"runs", "attempts", "ledger.jsonl", "transcript.jsonl.gz"} <= names
        assert {"attempts.json", "claims.json", "score.json"} <= names
        s = json.loads((dest / "score.json").read_text())
        assert s["claims_backed"] == 1 and s["cases_reproduced"] >= 1
        assert gzip.decompress((dest / "transcript.jsonl.gz").read_bytes())
    assert kinds(root).count("trial-exported") == 2
    assert make_runner(root, path).run() == 0
    assert kinds(root).count("trial-start") == 2
    st = trials.status(root, trials.load_plan(root, path))
    assert st["done"] == 2 and st["current"] is None and st["alive"] is False


def test_an_interrupted_trial_is_logged_and_rerun_with_a_new_id(root):
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    state = trials.State(root, trials.load_plan(root, path))
    state.add("trial-start", trial="17032-none-1", run_id="agent-19990101T000000Z")
    assert make_runner(root, path).run() == 0
    ev = events(root)
    assert [e["event"] for e in ev[1:]][:3] == ["plan-start", "trial-interrupted", "trial-start"]
    assert ev[2]["run_id"] == "agent-19990101T000000Z"
    assert ev[3]["run_id"] != "agent-19990101T000000Z"
    assert "trial-exported" in kinds(root)


def test_a_trial_interrupted_twice_stops_the_plan(root):
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    state = trials.State(root, trials.load_plan(root, path))
    for run_id in ("agent-19990101T000000Z", "agent-19990101T000001Z"):
        state.add("trial-start", trial="17032-none-1", run_id=run_id)
    assert make_runner(root, path).run() == 1
    assert events(root)[-1]["reason"] == "trial 17032-none-1 was interrupted twice"
    assert kinds(root).count("trial-start") == 2


@pytest.mark.parametrize(
    "over,expected",
    [
        ({"images": {"2.22.0": "sha256:" + "2" * 64}}, "image 2.22.0 is sha256:111"),
        ({"prompt_hash": "0" * 64}, "prompt hash"),
        ({"oversold_pin": "b" * 40}, "Oversold pin"),
    ],
)
def test_a_preflight_mismatch_stops_before_any_trial(root, over, expected):
    assert make_runner(root, write_plan(root, **over)).run() == 1
    assert "trial-start" not in kinds(root)
    assert expected in events(root)[-1]["reason"]


def test_a_postgres_that_does_not_answer_stops_the_plan_before_any_trial(root):
    checks = trials.Checks(
        engine_name=lambda: "colima-shortfall",
        image_id=lambda v, var: IMAGE,
        vm_free_bytes=lambda: 10**12,
        mac_free_bytes=lambda r: 10**12,
        oversold_running=lambda: False,
        postgres_answers=lambda port: False,
    )
    assert make_runner(root, write_plan(root), checks=checks).run() == 1
    assert "trial-start" not in kinds(root)
    assert (
        "Oversold's postgres does not answer on 127.0.0.1:55432, run sh scripts/oversold.sh up"
        in events(root)[-1]["reason"]
    )


def test_the_postgres_port_comes_from_the_oversold_env_file(tmp_path):
    assert trials.oversold_postgres_port(tmp_path) == 55432
    env = tmp_path / ".oversold" / ".env"
    env.parent.mkdir()
    env.write_text("POSTGRES_USER=oversold\nPOSTGRES_PORT=55433\n")
    assert trials.oversold_postgres_port(tmp_path) == 55433


def test_postgres_answers_only_while_something_listens_on_the_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        assert trials.postgres_answers(port)
    assert not trials.postgres_answers(port)


class Launched:
    def __init__(self, up_code=0):
        self.up_code = up_code
        self.calls = []

    def run(self, cmd, cwd=None):
        self.calls.append(("run", cmd, {"cwd": cwd}))
        return subprocess.CompletedProcess(cmd, self.up_code)

    def popen(self, cmd, **kw):
        self.calls.append(("popen", cmd, kw))
        return SimpleNamespace(pid=4242)


def test_the_launcher_brings_postgres_up_then_starts_the_plan_in_its_own_session(root):
    path = write_plan(root)
    fake = Launched()
    code = launch.launch(
        root, str(path), 3.0, run=fake.run, popen=fake.popen, which=lambda name: name
    )
    assert code == 0
    assert fake.calls[0] == ("run", ["sh", "scripts/oversold.sh", "up"], {"cwd": root})
    kind, cmd, kw = fake.calls[1]
    assert kind == "popen" and kw["start_new_session"] and kw["cwd"] == root
    assert cmd[1:] == ["-u", "-m", "shortfall.trials", "plan.yaml", "--raise-dollar-cap", "3.0"]
    kind, cmd, kw = fake.calls[2]
    assert cmd == ["caffeinate", "-ims", "-w", "4242"] and kw["start_new_session"]
    assert (root / "runs" / "trials" / "test-plan.pid").read_text() == "4242\n"
    assert (root / "runs" / "trials" / "test-plan.log").exists()


def test_the_launcher_does_not_start_the_plan_when_postgres_does_not_come_up(root):
    path = write_plan(root)
    fake = Launched(up_code=2)
    code = launch.launch(root, str(path), run=fake.run, popen=fake.popen, which=lambda n: n)
    assert code == 1 and [c[0] for c in fake.calls] == ["run"]
    assert not (root / "runs" / "trials" / "test-plan.pid").exists()


def test_the_launcher_refuses_while_the_plan_is_running(root):
    path = write_plan(root)
    pid = root / "runs" / "trials" / "test-plan.pid"
    pid.parent.mkdir(parents=True, exist_ok=True)
    pid.write_text(f"{os.getpid()}\n")
    fake = Launched()
    code = launch.launch(root, str(path), run=fake.run, popen=fake.popen, which=lambda n: n)
    assert code == 1 and fake.calls == []


def test_engine_and_disk_checks(root):
    checks = trials.Checks(
        engine_name=lambda: "desktop-linux",
        image_id=lambda v, var: IMAGE,
        vm_free_bytes=lambda: 1,
        mac_free_bytes=lambda r: 1,
        oversold_running=lambda: False,
    )
    assert make_runner(root, write_plan(root), checks=checks).run() == 1
    reason = events(root)[-1]["reason"]
    assert "engine reports desktop-linux" in reason and "the Mac has 0.0 GB free" in reason


def test_a_paid_plan_needs_dollar_room(root):
    path = write_plan(root, model="claude-haiku-5-5", script=None)
    assert make_runner(root, path, cap=0.0).run() == 1
    assert "no dollar room under the plan cap" in events(root)[-1]["reason"]


def test_a_billing_error_stops_the_plan_and_keeps_the_trial_local(root):
    class Broke(ScriptedModel):
        def reply(self, messages, tools):
            raise ModelUnavailable("billing error (402): payment required")

    path = write_plan(root)
    assert make_runner(root, path, model=lambda: Broke(replies=[])).run() == 1
    assert kinds(root)[-2:] == ["trial-kept-local", "plan-stop"]
    assert "billing error" in events(root)[-1]["reason"]
    assert not (root / "benchmark" / "export").exists()


def test_a_failed_scan_removes_the_export_and_stops(root):
    path = write_plan(root)
    runner = make_runner(root, path, scanner=lambda folder: ["score.json: holds a local path"])
    assert runner.run() == 1
    assert kinds(root)[-2:] == ["trial-export-failed", "plan-stop"]
    assert not (root / "benchmark" / "export" / "17032-none-1").exists()


def test_a_manual_check_trial_is_held_and_the_plan_goes_on(root, monkeypatch):
    real = trials.score_trial
    seen = []

    def held_first(r, records):
        out = real(r, records)
        if not seen:
            out["manual_check"] = [
                "no_orphaned_orders failed, covered only by a manual-check issue"
            ]
        seen.append(1)
        return out

    monkeypatch.setattr(trials, "score_trial", held_first)
    assert make_runner(root, write_plan(root)).run() == 0
    assert kinds(root).count("trial-held") == 1 and kinds(root).count("trial-exported") == 1
    assert not (root / "benchmark" / "export" / "17032-none-1").exists()


def test_claims_and_expected_checks_are_scored(root):
    replies = full_script()[:-1] + [
        reply(
            call(
                "finish",
                summary="x",
                claims=[
                    {
                        "attempt": 2,
                        "file": "packages/core/src/cart.ts",
                        "cause": "process-local-lock",
                    },
                    {"attempt": 1, "file": "packages/modules/x.ts", "cause": "per-line-check"},
                ],
            )
        )
    ]
    t, _, _ = trial(root, replies)
    t.run()
    s = score_trial(root, ledger.load(score.ledger_path_for(root)))
    assert (s["claims_backed"], s["claims_unbacked"]) == (1, 1)
    assert [c["why"] for c in s["claims"]] == ["violation on plain Medusa", "refused"]
    first = s["claims"][0]
    assert (
        first["diagnosis_after_results"]["grades"]["medusa-17032-last-unit"]["cause"] == "accepted"
    )
    assert first["prediction"] == {
        "file": "packages/core/src/cart.ts",
        "cause": "process-local-lock",
    }
    assert first["diagnosis_after_results"]["same_as_prediction"] is True
    assert s["claim_diagnoses_changed"] == sum(
        1
        for c in s["claims"]
        if c["prediction"] != {k: c["diagnosis_after_results"][k] for k in ("file", "cause")}
    )
    assert s["expected_check"] == {"hits": 1, "of": 1}
    assert s["cases"]["medusa-17032-last-unit"]["reproduced"] is True
    assert s["cases"]["medusa-17032-last-unit"]["runs_to_first"] == 33
    assert (s["attempts"], s["refused"], s["turns"]) == (2, 1, 6)


def test_the_export_scan(root, monkeypatch):
    monkeypatch.setattr(trials, "gitleaks_findings", lambda r, folder: [])
    (root / "snapshots" / "medusa-2.22.0" / "packages" / "flow.ts").write_text(
        "export const zebrafishWorkflow = 1\n"
    )
    words = ["zebrafish"]
    folder = root / "runs" / "scan"
    folder.mkdir(parents=True)
    quotes = trials.Quotes(root)
    clean = '{"content": "    12\\texport const zebrafishWorkflow = 1"}\n'
    (folder / "a.jsonl").write_text(clean)
    (folder / "b.json.gz").write_bytes(gzip.compress("a \u2014 quoted dash\n".encode()))
    assert trials.scan_export(root, folder, quotes, None, words) == []
    assert trials.scan_export(root, folder, quotes, None, None) == [
        "no private word list at .git/info/private-words"
    ]
    (folder / "c.json").write_text('{"note": "see my zebrafish"}\n')
    (folder / "d.json").write_text('{"note": "a \u2014 b"}\n')
    (folder / "e.json").write_text(json.dumps({"path": str(Path.home()) + "/x"}))
    (folder / "f.json").write_text('{"k": "sk-ant-api03-abcdefghijklmnopqrstuv"}\n')
    (folder / "g.json").write_text('{"k": "secret-value-1234"}\n')
    found = trials.scan_export(root, folder, quotes, "secret-value-1234", words)
    assert any(p.startswith("c.json: 'zebrafish'") for p in found)
    assert "d.json: holds a raw dash character" in found
    assert "e.json: holds a local path" in found
    assert "f.json: holds something that looks like a key" in found
    assert "g.json: holds the API key" in found


def test_private_words_come_from_a_local_file(root):
    assert trials.private_words(root) is None
    (root / ".git" / "info").mkdir(parents=True)
    (root / ".git" / "info" / "private-words").write_text("Alpha\n\nbeta gamma\n")
    assert trials.private_words(root) == ["alpha", "beta gamma"]


def test_plans_are_checked(root):
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, mode="unguided"))
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, dollar_cap=21))
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, order="random"))


@pytest.mark.skipif(not (ROOT / "snapshots" / "issues").exists(), reason="no local snapshots")
def test_the_committed_guided_plan():
    plan = trials.load_plan(ROOT, ROOT / "benchmark" / "agent" / "plans" / "guided-haiku-1.yaml")
    assert (plan.model, plan.mode, plan.trials_per_cell) == ("claude-haiku-5-5", "guided", 3)
    assert [c.label for c in plan.cells] == [
        "16502-none",
        "16502-history",
        "17032-none",
        "17032-history",
    ]
    assert (plan.caps.runs, plan.caps.attempts, plan.caps.turns, plan.caps.dollars) == (
        300,
        12,
        60,
        1.0,
    )
    v1 = (ROOT / "benchmark" / "agent" / "guided-haiku-1" / "prompts.sha256").read_text()
    assert plan.dollar_cap == 3.0 and plan.prompt_hash == v1.splitlines()[0]
    assert plan.images["2.22.0"].startswith("sha256:c48358f7")


@pytest.mark.skipif(not (ROOT / "snapshots" / "issues").exists(), reason="no local snapshots")
@pytest.mark.parametrize(
    "name,mode,labels",
    [
        ("unguided-haiku-1", "unguided", ["unguided-none", "unguided-history"]),
        ("guided-haiku-2", "guided", ["17032-none", "17032-history"]),
    ],
)
def test_the_v2_plans(name, mode, labels):
    plan = trials.load_plan(ROOT, ROOT / "benchmark" / "agent" / "plans" / f"{name}.yaml")
    assert (plan.model, plan.mode, plan.trials_per_cell) == ("claude-haiku-5-5", mode, 3)
    assert [c.label for c in plan.cells] == labels
    assert (plan.caps.runs, plan.caps.attempts, plan.caps.turns, plan.caps.dollars) == (
        300,
        30,
        100,
        1.0,
    )
    assert plan.dollar_cap == 3.0 and plan.prompt_hash == freeze.recorded_hash(ROOT)
    assert plan.images["2.22.0-pr-16961"].startswith("sha256:0075cea1")


def test_model_text_matches_and_the_local_allow_list(root, monkeypatch):
    monkeypatch.setattr(trials, "gitleaks_findings", lambda r, folder: [])
    folder = root / "benchmark" / "agent" / "p" / "t-1"
    folder.mkdir(parents=True)
    said = "Here the zebrafish rests on the report. Nothing else."
    reply_event = {"event": "reply", "turn": 1, "message": {"role": "assistant", "content": said}}
    (folder / "transcript.jsonl.gz").write_bytes(gzip.compress(json.dumps(reply_event).encode()))
    (folder / "claims.json").write_text(json.dumps({"summary": said}))
    (folder / "notes.json").write_text(json.dumps({"x": "a zebrafish from the harness"}))
    quotes = trials.Quotes(root)
    found = trials.scan_export(root, folder, quotes, None, ["zebrafish"])
    assert (
        "model text: claims.json: 'zebrafish' in: Here the zebrafish rests on the report." in found
    )
    assert "notes.json: 'zebrafish' that is not a quote of Medusa or a report" in found
    allow = [
        {"path": "benchmark/agent/p/t-1/claims.json", "sentence": "the zebrafish rests on"},
        {"path": "benchmark/agent/p/t-1/transcript.jsonl.gz", "sentence": "the zebrafish rests on"},
    ]
    found = trials.scan_export(root, folder, quotes, None, ["zebrafish"], allow)
    assert found == ["notes.json: 'zebrafish' that is not a quote of Medusa or a report"]


def test_a_trial_with_only_model_text_matches_is_held_and_the_plan_goes_on(root):
    calls = []

    def scanner(folder):
        calls.append(folder.name)
        if len(calls) == 1:
            return ["model text: claims.json: 'zebrafish' in: my zebrafish idea."]
        return []

    assert make_runner(root, write_plan(root), scanner=scanner).run() == 0
    held = [e for e in events(root) if e["event"] == "trial-held"]
    assert held[0]["notes"] == ["model text: claims.json: 'zebrafish' in: my zebrafish idea."]
    assert kinds(root).count("trial-exported") == 1 and kinds(root)[-1] == "plan-done"
    assert not (root / "benchmark" / "export" / "17032-none-1").exists()


def test_a_path_match_still_stops_the_plan(root):
    def scanner(folder):
        return ["model text: a.json: 'zebrafish' in: x.", "a.json: holds a local path"]

    assert make_runner(root, write_plan(root), scanner=scanner).run() == 1
    assert kinds(root)[-2:] == ["trial-export-failed", "plan-stop"]


def test_a_transcript_that_quotes_an_enterprise_file_holds_the_trial(root, monkeypatch):
    monkeypatch.setattr(trials, "gitleaks_findings", lambda r, folder: [])
    (root / "benchmark" / "snapshots").mkdir(parents=True, exist_ok=True)
    (root / "benchmark" / "snapshots" / "enterprise-2.22.0.json").write_text(
        json.dumps({"paths": ["packages/rbac/", "packages/core/lock.ts"]})
    )
    folder = root / "runs" / "ee"
    folder.mkdir(parents=True)
    events = [
        {
            "event": "tool",
            "call": "a",
            "content": "error: packages/rbac/x.ts: this file is not available",
        },
        {"event": "tool", "call": "b", "content": "1 matches\\npackages/core/cart.ts:3: x"},
    ]
    blob = "\n".join(json.dumps(e) for e in events).replace("\\\\n", "\\n")
    (folder / "transcript.jsonl.gz").write_bytes(gzip.compress(blob.encode()))
    quotes = trials.Quotes(root)
    assert trials.scan_export(root, folder, quotes, None, []) == []
    events.append(
        {"event": "tool", "call": "c", "content": "packages/core/lock.ts, lines 1 to 2 of 2"}
    )
    events.append(
        {"event": "tool", "call": "d", "content": "2 matches\npackages/rbac/y.ts:4: role"}
    )
    blob = "\n".join(json.dumps(e) for e in events)
    (folder / "transcript.jsonl.gz").write_bytes(gzip.compress(blob.encode()))
    assert trials.scan_export(root, folder, quotes, None, []) == [
        "enterprise: transcript.jsonl.gz: quotes packages/core/lock.ts",
        "enterprise: transcript.jsonl.gz: quotes packages/rbac/",
    ]


def test_an_enterprise_hold_keeps_the_plan_going(root):
    calls = []

    def scanner(folder):
        calls.append(folder.name)
        return ["enterprise: transcript.jsonl.gz: quotes packages/rbac/"] if len(calls) == 1 else []

    assert make_runner(root, write_plan(root), scanner=scanner).run() == 0
    assert kinds(root).count("trial-held") == 1 and kinds(root)[-1] == "plan-done"
    assert (root / "benchmark" / "export" / "prompts.sha256").exists()


def write_v2_plan(root: Path, **over) -> Path:
    pin = (root / "oversold.lock").read_text().split("commit=")[1].strip()
    data = {
        "schema": trials.PLAN_SCHEMA_V2,
        "name": "mix",
        "model": "scripted",
        "script": "runs/script.json",
        "agent_caps": {"runs": 300, "attempts": 30, "turns": 100, "dollars": 1},
        "dollar_cap": 3,
        "oversold_pin": pin,
        "images": {"2.22.0": IMAGE},
        "export_root": "benchmark/export",
        "baseline_root": "benchmark/baselines",
        "arms": [
            {
                "name": "unguided-none",
                "kind": "agent",
                "mode": "unguided",
                "feedback": "none",
                "prompts": "v2",
                "prompt_hash": freeze.prompt_hash(root),
                "trials": [4, 5],
            },
            {
                "name": "nomenu-none",
                "kind": "agent",
                "mode": "unguided",
                "feedback": "none",
                "prompts": "v2-nomenu",
                "prompt_hash": freeze.prompt_hash(root, "v2-nomenu"),
                "trials": [1],
            },
            {"name": "grid", "kind": "baseline", "method": "grid", "seeds": [4]},
        ],
        "order": ["nomenu-none-1", "unguided-none-4", "grid-seed-4", "unguided-none-5"],
        "report": ["per case and arm: trials that reproduced it"],
        **over,
    }
    path = root / "plan2.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def test_a_v2_plan_lists_every_arm_in_its_order(root):
    plan = trials.load_plan(root, write_v2_plan(root))
    specs = trials.trial_order(plan)
    assert [s.id for s in specs] == [
        "nomenu-none-1",
        "unguided-none-4",
        "grid-seed-4",
        "unguided-none-5",
    ]
    assert [s.kind for s in specs] == ["agent", "agent", "baseline", "agent"]
    assert specs[0].variant == "v2-nomenu" and specs[2].method == "grid" and specs[2].number == 4
    assert plan.report == ["per case and arm: trials that reproduced it"]
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_v2_plan(root, order=["nomenu-none-1"]))


def test_a_v2_plan_runs_agent_arms_with_their_prompts(root, monkeypatch):
    path = write_v2_plan(
        root, order=["nomenu-none-1", "unguided-none-4", "unguided-none-5", "grid-seed-4"]
    )
    runner = make_runner(root, path)
    seen = []
    monkeypatch.setattr(runner, "run_baseline", lambda spec: seen.append(spec.id) or 0)
    nomenu_script = [
        reply(
            call(
                "submit_attempt",
                file="packages/core/src/cart.ts",
                expected_check="no_oversell",
                hypothesis="Two servers each reserve the last unit.",
                scenario=SCENARIO,
            )
        ),
        reply(
            call(
                "finish", summary="x", claims=[{"attempt": 1, "file": "packages/core/src/cart.ts"}]
            )
        ),
    ]
    scripts = iter([nomenu_script, script(), script()])
    runner.make_model = lambda spec=None: ScriptedModel(replies=next(scripts))
    assert runner.run() == 0
    assert seen == ["grid-seed-4"]
    exported = [
        e["trial"]
        for e in trials.State(root, runner.plan).events()
        if e["event"] == "trial-exported"
    ]
    assert exported == ["nomenu-none-1", "unguided-none-4", "unguided-none-5"]
    assert (root / "benchmark" / "export" / "prompts.sha256").exists()
    assert (root / "benchmark" / "export" / "prompts-v2-nomenu.sha256").exists()
    first = json.loads((root / "benchmark" / "export" / "nomenu-none-1" / "score.json").read_text())
    assert first["claims_backed"] == 1


def test_the_baseline_command_and_its_stamp(root, tmp_path, monkeypatch):
    fake = tmp_path / "fake_sweep.py"
    fake.write_text(
        "import sys\n"
        "print('sweep: wrote 3 grid candidates to runs/sweep/20990101T000000Z, list sha256 abc')\n"
        "print(' '.join(sys.argv[1:]))\n"
        "sys.exit(int(open(sys.argv[0] + '.code').read()))\n"
    )
    (tmp_path / "fake_sweep.py.code").write_text("0")
    runner = make_runner(root, write_v2_plan(root))
    runner.sweep_command = [sys.executable, str(fake)]
    finished = []
    monkeypatch.setattr(
        runner, "finish_baseline", lambda spec, run_id, records: finished.append(run_id) or 0
    )
    spec = next(s for s in runner.plan.specs if s.kind == "baseline")
    assert runner.run_baseline(spec) == 0
    assert finished == ["20990101T000000Z"]
    log = (runner.state.folder / "grid-seed-4.log").read_text()
    assert "--mode grid --max-runs 300 --order-seed 4" in log
    (tmp_path / "fake_sweep.py.code").write_text("3")
    assert runner.run_baseline(spec) == 1
    assert [e["event"] for e in runner.state.events()][-2:] == ["trial-kept-local", "plan-stop"]
    assert "uncovered failure" in runner.state.events()[-1]["reason"]


def test_a_baseline_trial_exports_in_the_baseline_layout(root):
    source = ROOT / "benchmark" / "baselines" / "2004ed5" / "grid-seed-1"
    records = [json.loads(x) for x in (source / "ledger.jsonl").read_text().splitlines()]
    trial_line = next(r for r in records if r.get("kind") == "trial")
    stamp = trial_line["attempt_id"].removesuffix("-trial")
    sweep = root / "runs" / "sweep" / stamp
    sweep.mkdir(parents=True)
    for name in trial_line["candidate_names"]:
        shutil.copy(source / "candidates" / f"{name}.yaml", sweep)

    def exporter(folder, dest):
        dest.mkdir(parents=True)

    dest = root / "benchmark" / "baselines" / "grid-seed-1"
    summary = trials.export_baseline(root, stamp, dest, records, exporter)
    assert summary["runs_used"] == 298 and summary["cases_reproduced"] == 3
    assert len(list((dest / "candidates").iterdir())) == 32
    assert len(list((dest / "runs").iterdir())) > 0


NO_OVERSELL = "no_oversell failed 1 of 13 runs on plain Medusa 2.22.0: violation"
ONE_ORDER = (
    "one_order_per_cart failed 1 of 13 runs on plain Medusa 2.22.0: violation, cause not "
    "isolated, no case's scoring control clears it"
)


def held_run(root, monkeypatch, notes=(NO_OVERSELL,)):
    real = trials.score_trial

    def held_first(r, records):
        out = real(r, records)
        if not getattr(held_first, "done", False):
            out["manual_check"] = list(notes)
            held_first.done = True
        return out

    monkeypatch.setattr(trials, "score_trial", held_first)
    review = trials.Runner.review_held
    monkeypatch.setattr(trials.Runner, "review_held", lambda self: 0)
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    assert make_runner(root, path).run() == 0
    monkeypatch.setattr(trials, "score_trial", real)
    monkeypatch.setattr(trials.Runner, "review_held", review)
    event = next(e for e in events(root) if e["event"] == "trial-held")
    ledger_path = score.ledger_path_for(root)
    lines = []
    for line in ledger_path.read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") == "final" and r["attempt_id"].startswith(event["run_id"]):
            r["manual_check"] = list(notes)
        lines.append(json.dumps(r))
    ledger_path.write_text("\n".join(lines) + "\n")
    return path


class FailsOn(Oversold):
    def __init__(self, failing, **kw):
        super().__init__(**kw)
        self.failing = failing

    def run(self, scenario, runs, version):
        out = super().run(scenario, runs, version)
        if scenario.stem.endswith(self.failing):
            src = PLAIN_HISTORY
            out = score.RunSet(
                folder=out.folder, histories=[json.loads(json.dumps(src)) for _ in range(runs)]
            )
        return out


PLAIN_HISTORY = json.loads(
    (ROOT / "tests" / "data" / "histories" / "five-checks-fail.json").read_text()
)


def test_a_held_trial_whose_failure_shows_on_plain_only_is_published_with_review(root, monkeypatch):
    path = held_run(root, monkeypatch)
    runner = make_runner(root, path)
    assert runner.review_held() == 0
    ev = events(root)
    assert ev[-1]["event"] == "trial-exported" and ev[-1]["note"] == "published after review"
    review = json.loads(
        (root / "benchmark" / "export" / "17032-none-1" / "review" / "review.json").read_text()
    )
    sets = review["attempts"][0]["sets"]
    assert sets["plain"]["runs"] == 60 and sets["plain"]["fails"]["no_oversell"] == 60
    assert (
        sets["pr-17420"]["fails"]["no_oversell"] == 0 and sets["redis"]["fails"]["no_oversell"] == 0
    )
    assert review["label"] == "covered by #17032, rare in this scenario"


def test_a_failure_with_redis_in_a_review_stops_everything(root, monkeypatch):
    path = held_run(root, monkeypatch)
    runner = make_runner(root, path)
    runner.oversold = FailsOn("redis-control", ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 1
    assert [e["event"] for e in events(root)][-2:] == ["review-stop", "plan-stop"]
    assert not (root / "benchmark" / "export" / "17032-none-1").exists()


def held_final(root):
    run_id = next(e for e in events(root) if e["event"] == "trial-held")["run_id"]
    return next(
        r
        for r in ledger.load(score.ledger_path_for(root))
        if r.get("kind") == "final" and r["attempt_id"].startswith(run_id)
    )


def test_a_hold_only_for_one_order_per_cart_on_two_in_memory_servers_waits_for_hand_review(
    root, monkeypatch
):
    path = held_run(root, monkeypatch, [ONE_ORDER])
    runner = make_runner(root, path)
    runner.oversold = FailsOn("pr-17420-control", ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 0
    ev = events(root)[-1]
    assert ev["event"] == "review-by-hand" and ev["reason"] == trials.HAND_REVIEW
    assert ev["attempts"] == [held_final(root)["attempt_id"]]
    assert runner.oversold.calls == []
    assert not (root / "benchmark" / "export" / "17032-none-1").exists()
    assert make_runner(root, path).review_held() == 0
    assert kinds(root).count("review-by-hand") == 1


def test_a_one_order_per_cart_hold_on_one_server_still_gets_the_automatic_review(root, monkeypatch):
    path = held_run(root, monkeypatch, [ONE_ORDER])
    scenario = root / held_final(root)["scenario"]
    data = yaml.safe_load(scenario.read_text())
    data["target"]["servers"] = 1
    for item in [*data["carts"].values(), *data["race"]]:
        item["server"] = 1
    scenario.write_text(yaml.safe_dump(data, sort_keys=False))
    runner = make_runner(root, path)
    runner.oversold = FailsOn("pr-17420-control", ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 1
    assert [e["event"] for e in events(root)][-2:] == ["review-stop", "plan-stop"]


def test_a_hold_with_another_rule_besides_one_order_per_cart_gets_the_automatic_review(
    root, monkeypatch
):
    path = held_run(root, monkeypatch, [ONE_ORDER, NO_OVERSELL])
    runner = make_runner(root, path)
    runner.oversold = FailsOn("pr-17420-control", ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 1
    assert [e["event"] for e in events(root)][-2:] == ["review-stop", "plan-stop"]


def test_a_held_trial_whose_failure_never_shows_on_plain_stays_held(root, monkeypatch):
    path = held_run(root, monkeypatch)
    runner = make_runner(root, path)

    class Passes(Oversold):
        def run(self, scenario, runs, version):
            out = super().run(Path(str(scenario).replace(".yaml", "-control.yaml")), runs, version)
            return out

    runner.oversold = Passes(ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 0
    assert events(root)[-1]["event"] == "review-kept-held"


def test_the_local_word_rule_allows_model_files_under_benchmark_agent(root, monkeypatch):
    monkeypatch.setattr(trials, "gitleaks_findings", lambda r, folder: [])
    rules = [
        {
            "word": "zebrafish",
            "under": "benchmark/agent/",
            "files": ["claims.json", "transcript.jsonl.gz"],
        }
    ]
    folder = root / "benchmark" / "agent" / "p" / "t-1"
    folder.mkdir(parents=True)
    said = "My zebrafish idea held up. Nothing else."
    event = {"event": "reply", "turn": 1, "message": {"role": "assistant", "content": said}}
    (folder / "transcript.jsonl.gz").write_bytes(gzip.compress(json.dumps(event).encode()))
    (folder / "claims.json").write_text(json.dumps({"summary": said}))
    found, allowed = [], []
    found = trials.scan_export(
        root, folder, trials.Quotes(root), None, ["zebrafish"], [], rules, allowed
    )
    assert found == []
    assert [a["path"] for a in allowed] == [
        "benchmark/agent/p/t-1/claims.json",
        "benchmark/agent/p/t-1/transcript.jsonl.gz",
    ]
    (folder / "attempts.json").write_text(json.dumps({"hypothesis": said}))
    found = trials.scan_export(
        root, folder, trials.Quotes(root), None, ["zebrafish"], [], rules, []
    )
    assert found == ["model text: attempts.json: 'zebrafish' in: My zebrafish idea held up."]
    other = root / "runs" / "elsewhere"
    other.mkdir(parents=True)
    (other / "claims.json").write_text(json.dumps({"summary": said}))
    found = trials.scan_export(root, other, trials.Quotes(root), None, ["zebrafish"], [], rules, [])
    assert found == ["claims.json: 'zebrafish' that is not a quote of Medusa or a report"]


@pytest.mark.skipif(not (ROOT / "snapshots" / "issues").exists(), reason="no local snapshots")
def test_the_scale_10_plan():
    plan = trials.load_plan(ROOT, ROOT / "benchmark" / "agent" / "plans" / "scale-10.yaml")
    specs = trials.trial_order(plan)
    assert len(specs) == 38
    assert [s.id for s in specs[:3]] == ["nomenu-none-1", "nomenu-none-2", "nomenu-none-3"]
    for n in range(4, 11):
        block = [s.id for s in specs[3 + (n - 4) * 5 : 3 + (n - 3) * 5]]
        assert block == [
            f"unguided-none-{n}",
            f"unguided-history-{n}",
            f"grid-seed-{n}",
            f"random-seed-{n}",
            f"nomenu-none-{n}",
        ]
    agents = [s for s in specs if s.kind == "agent"]
    assert {(s.variant, s.prompt_hash) for s in agents} == {
        ("v2", freeze.recorded_hash(ROOT)),
        ("v2-nomenu", freeze.recorded_hash(ROOT, "v2-nomenu")),
    }
    assert (plan.caps.runs, plan.caps.attempts, plan.caps.turns, plan.caps.dollars) == (
        300,
        30,
        100,
        1.0,
    )
    assert plan.baseline_runs == 300 and plan.dollar_cap == 3.0 and plan.model == "claude-haiku-5-5"
    assert len(plan.report) == 7


def test_a_pause_file_stops_the_plan_before_the_next_trial(root):
    path = write_plan(root)
    runner = make_runner(root, path)
    runner.state.pause_path.write_text("")
    assert runner.run() == 0
    assert kinds(root)[-1] == "plan-paused" and "trial-start" not in kinds(root)
    assert trials.status(root, runner.plan)["pause_file"] is True
    runner.state.pause_path.unlink()
    assert make_runner(root, path).run() == 0
    assert kinds(root).count("trial-exported") == 2


def kept_local(root, path):
    state = trials.State(root, trials.load_plan(root, path))
    state.add("trial-start", trial="17032-none-1", run_id="agent-19990101T000000Z")
    state.add("trial-end", trial="17032-none-1", run_id="agent-19990101T000000Z", reason="x")
    state.add("trial-kept-local", trial="17032-none-1", run_id="agent-19990101T000000Z")


def test_a_kept_local_trial_is_skipped_until_it_is_reopened(root):
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    kept_local(root, path)
    assert make_runner(root, path).run() == 0
    assert kinds(root).count("trial-start") == 1
    plan = trials.load_plan(root, path)
    assert trials.reopen(root, plan, "17032-none-1", "stopped by a rule") is None
    assert "reopened before" in trials.reopen(root, plan, "17032-none-1", "again")
    assert make_runner(root, path).run() == 0
    ev = events(root)
    starts = [e["run_id"] for e in ev if e["event"] == "trial-start"]
    assert len(starts) == 2 and starts[1] != "agent-19990101T000000Z"
    assert ev[-2]["event"] == "trial-exported" and ev[-2]["run_id"] == starts[1]
    assert "is exported" in trials.reopen(root, plan, "17032-none-1", "again")
    assert "has no trial" in trials.reopen(root, plan, "17032-none-9", "x")


def test_a_reopened_trial_counts_as_one_interrupt(root):
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    kept_local(root, path)
    plan = trials.load_plan(root, path)
    assert trials.reopen(root, plan, "17032-none-1", "stopped by a rule") is None
    trials.State(root, plan).add(
        "trial-start", trial="17032-none-1", run_id="agent-19990101T000001Z"
    )
    assert make_runner(root, path).run() == 1
    assert events(root)[-1]["reason"] == "trial 17032-none-1 was interrupted twice"


def test_a_trial_held_by_the_local_shape_list_is_not_reviewed(root, monkeypatch):
    path = held_run(root, monkeypatch)
    state = trials.State(root, trials.load_plan(root, path))
    held = next(e for e in state.events() if e["event"] == "trial-held")
    state.add(
        "trial-held",
        trial="17032-none-1",
        run_id=held["run_id"],
        notes=[f"{trials.HELD_NOTE}no_missing_orders failed 1 of 3 runs in the screen set"],
    )
    lines = state.events_path.read_text().splitlines()
    first = next(i for i, x in enumerate(lines) if '"trial-held"' in x)
    state.events_path.write_text("\n".join(lines[:first] + lines[first + 1 :]) + "\n")
    runner = make_runner(root, path)
    runner.oversold = FailsOn("redis-control", ledger_path=score.ledger_path_for(root))
    assert runner.review_held() == 0
    assert kinds(root)[-1] == "trial-held"


def test_a_review_can_carry_its_own_label(root, monkeypatch):
    path = held_run(root, monkeypatch)
    runner = make_runner(root, path)
    real = runner.review_attempt

    def labelled(spec, final):
        return dict(real(spec, final), label="covered by two issues together")

    runner.review_attempt = labelled
    assert runner.review_held() == 0
    review = json.loads(
        (root / "benchmark" / "export" / "17032-none-1" / "review" / "review.json").read_text()
    )
    assert review["label"] == "covered by two issues together"


def test_a_held_trial_published_after_review_counts_once_in_the_status(root, monkeypatch):
    path = held_run(root, monkeypatch)
    assert make_runner(root, path).review_held() == 0
    assert kinds(root).count("trial-held") == kinds(root).count("trial-exported") == 1
    st = trials.status(root, trials.load_plan(root, path))
    assert st["done"] == 1 and st["done_trials"] == ["17032-none-1"]


def budget_arm(root, trials_=(1,), model=None):
    arm = {
        "name": "budget-none",
        "kind": "agent",
        "mode": "unguided",
        "feedback": "none",
        "prompts": "v2-budget",
        "prompt_hash": freeze.prompt_hash(root, "v2-budget"),
        "trials": list(trials_),
    }
    if model:
        arm["model"] = model
    return arm


def test_an_arm_can_name_its_own_model(root):
    sonnet = dict(budget_arm(root), name="sonnet-none", prompts="v2", model="claude-sonnet-5-5")
    sonnet["prompt_hash"] = freeze.prompt_hash(root)
    path = write_v2_plan(
        root, arms=[budget_arm(root), sonnet], order=["budget-none-1", "sonnet-none-1"]
    )
    plan = trials.load_plan(root, path)
    first, second = trials.trial_order(plan)
    assert first.model is None and trials.model_of(plan, first) == "scripted"
    assert second.model == "claude-sonnet-5-5"
    assert trials.model_of(plan, second) == "claude-sonnet-5-5"
    bad = dict(sonnet, model="claude-unknown")
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_v2_plan(root, arms=[bad], order=["sonnet-none-1"]))


def test_a_budget_arm_runs_through_the_plan_and_records_its_gate(root):
    (root / freeze.HASH_FILES["v2-budget"]).write_text(freeze.hash_file_text(root, "v2-budget"))
    path = write_v2_plan(
        root,
        arms=[budget_arm(root)],
        order=["budget-none-1"],
        agent_caps={"runs": 300, "attempts": 30, "turns": 3, "dollars": 1},
    )
    gated = [
        reply(call("finish", summary="x", claims=[])),
        Reply(text="I am done."),
        reply(call("finish", summary="x", claims=[])),
    ]
    runner = make_runner(root, path, model=lambda: ScriptedModel(replies=list(gated)))
    assert runner.run() == 0
    s = json.loads((root / "benchmark" / "export" / "budget-none-1" / "score.json").read_text())
    assert s["end_reason"] == "finished by the model" and s["gate_answers"] == 2
    assert (root / "benchmark" / "export" / "prompts-v2-budget.sha256").exists()


def test_an_absolute_export_folder_is_refused(root, tmp_path):
    outside = str(tmp_path / "outside")
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, export_root=outside))
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_v2_plan(root, baseline_root=outside))


def test_an_export_folder_with_dot_dot_or_outside_benchmark_is_refused(root):
    for value in ("benchmark/../runs", "benchmark/agent/../../outside", "../outside", "runs/x"):
        with pytest.raises(trials.PlanError):
            trials.load_plan(root, write_plan(root, export_root=value))
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, export_root="benchmark"))


def test_an_export_folder_through_a_symlink_is_refused(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (root / "benchmark" / "agent").mkdir(parents=True, exist_ok=True)
    (root / "benchmark" / "agent" / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, export_root="benchmark/agent/link"))
    assert (outside / "keep.txt").read_text() == "keep"


def test_arm_and_trial_names_must_be_plain(root):
    arms = yaml.safe_load(write_v2_plan(root).read_text())["arms"]
    for bad in ("../x", "Unguided-none", "a_b", "a/b", ""):
        changed = [dict(arms[0], name=bad), *arms[1:]]
        order = [f"{bad}-4", "nomenu-none-1", f"{bad}-5", "grid-seed-4"]
        with pytest.raises(trials.PlanError):
            trials.load_plan(root, write_v2_plan(root, arms=changed, order=order))
    changed = [dict(arms[0], trials=["4/../x", 5]), *arms[1:]]
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_v2_plan(root, arms=changed))
    with pytest.raises(trials.PlanError):
        trials.load_plan(root, write_plan(root, cells=[{"issue": "1/..", "feedback": "none"}]))


def test_a_symlinked_trial_folder_is_never_replaced_or_followed(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    export = root / "benchmark" / "export"
    export.mkdir(parents=True)
    (export / "17032-none-1").symlink_to(outside, target_is_directory=True)
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    assert make_runner(root, path).run() == 1
    assert (outside / "keep.txt").read_text() == "keep"
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]
    assert (export / "17032-none-1").is_symlink()
    failed = [e for e in events(root) if e["event"] == "trial-export-failed"]
    assert failed[0]["trial"] == "17032-none-1"
    assert not list(export.glob(".*" + trials.STAGE_SUFFIX))


def test_an_existing_trial_folder_is_never_replaced(root):
    dest = root / "benchmark" / "export" / "17032-none-1"
    dest.mkdir(parents=True)
    (dest / "keep.txt").write_text("keep")
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    assert make_runner(root, path).run() == 1
    assert sorted(p.name for p in dest.iterdir()) == ["keep.txt"]
    failed = [e for e in events(root) if e["event"] == "trial-export-failed"]
    assert "already exists, nothing was replaced" in failed[0]["problems"][0]
    assert not list(dest.parent.glob(".*" + trials.STAGE_SUFFIX))


def test_an_export_is_built_beside_its_folder_and_renamed_into_place(root):
    seen = []
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    runner = make_runner(root, path)
    real = runner.exporter

    def exporter(folder, dest):
        seen.append(dest)
        real(folder, dest)

    runner.exporter = exporter
    assert runner.run() == 0
    dest = root / "benchmark" / "export" / "17032-none-1"
    assert seen and all(p.parent.parent == trials.stage_path(dest) for p in seen)
    assert (dest / "score.json").exists() and not trials.stage_path(dest).exists()


def test_a_rejected_export_leaves_no_folder_and_no_staging(root):
    path = write_plan(root, cells=[{"issue": 17032, "feedback": "none"}])
    runner = make_runner(root, path, scanner=lambda folder: ["score.json: holds a local path"])
    assert runner.run() == 1
    export = root / "benchmark" / "export"
    assert not (export / "17032-none-1").exists()
    assert not list(export.glob(".*" + trials.STAGE_SUFFIX))


def test_a_scan_of_a_staged_export_reports_final_paths(root):
    dest = root / "benchmark" / "agent" / "plan-x" / "trial-1"
    assert trials.final_place(trials.stage_path(dest)) == dest
    assert trials.final_place(dest) == dest
    stage = trials.stage_path(dest)
    stage.mkdir(parents=True)
    (root / "runs" / "trials").mkdir(parents=True, exist_ok=True)
    (stage / "claims.json").write_text('{"summary": "the word secretword here"}')
    found = trials.scan_export(root, stage, trials.Quotes(root), None, ["secretword"], place=dest)
    assert any(p.startswith("claims.json") for p in found)
    allow = [
        {
            "path": "benchmark/agent/plan-x/trial-1/claims.json",
            "sentence": "the word secretword here",
        }
    ]
    found = trials.scan_export(
        root, stage, trials.Quotes(root), None, ["secretword"], allow, place=dest
    )
    assert not any("secretword" in p for p in found)


def test_a_staging_folder_outside_benchmark_or_a_symlink_is_never_removed(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    export = root / "benchmark" / "export"
    export.mkdir(parents=True)
    stage = trials.stage_path(export / "17032-none-1")
    stage.symlink_to(outside, target_is_directory=True)
    with pytest.raises(trials.ExportError):
        trials.remove_stage(root, stage)
    with pytest.raises(trials.ExportError):
        trials.remove_stage(root, outside)
    assert (outside / "keep.txt").read_text() == "keep"


def test_a_claim_never_replaces_the_prediction_or_the_named_place_grades(root):
    replies = full_script()[:-1] + [
        reply(
            call(
                "finish",
                summary="x",
                claims=[
                    {
                        "attempt": 2,
                        "file": "packages/modules/inventory/src/services/inventory-module.ts",
                        "cause": "stale-counter-write",
                    }
                ],
            )
        )
    ]
    t, _, _ = trial(root, replies)
    t.run()
    records = ledger.load(score.ledger_path_for(root))
    before = score_trial(root, records)
    case = before["cases"]["medusa-17032-last-unit"]
    prediction = next(r for r in records if r.get("kind") == "prediction" and r["attempt"] == 2)
    assert (case["file"], case["cause"]) == (prediction["file"], prediction["cause"])
    claim = before["claims"][0]
    assert claim["prediction"] == {"file": prediction["file"], "cause": prediction["cause"]}
    assert claim["diagnosis_after_results"]["file"].endswith("inventory-module.ts")
    assert claim["diagnosis_after_results"]["grades"]["medusa-17032-last-unit"]["file"] == (
        "accepted"
    )
    late = dict(prediction, file="packages/modules/inventory/src/services/inventory-module.ts")
    after = score_trial(root, [*records, late])
    assert after["cases"] == before["cases"]
    assert after["attempt_list"] == before["attempt_list"]
    assert after["claims"][0]["prediction"] == claim["prediction"]
