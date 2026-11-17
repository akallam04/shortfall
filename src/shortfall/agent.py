import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import yaml

from shortfall import ledger, score
from shortfall.answers import load_causes
from shortfall.budget import CapReached, from_flags
from shortfall.spend import Meter, Usage, now
from shortfall.tools import Snapshot, ToolError

VERSION = "2.22.0"
READ_LINES = 200
RESULT_CHARS = 12_000
RUN_CAP = 300
ATTEMPT_CAP = 12
TURN_CAP = 60
KEEP_TURNS = 6
HYPOTHESIS_CHARS = 1_200
CHARS_PER_TOKEN = 3.5
PROMPTS = Path(__file__).resolve().parent / "prompts"
HARNESS_ROWS = ("| `target.variant` |", "| `target.locking` |")

TOOLS = [
    {
        "name": "list_files",
        "description": "List the files and folders directly under a folder of the source code.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Folder, like packages"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": f"Read numbered lines of a source file, at most {READ_LINES} per call.",
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
        "description": "Search the source code for plain text, case-sensitive, at most 50 matches.",
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
        "cause id, a short paragraph with your hypothesis, and the scenario YAML that tests it.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "One source path, like packages/..."},
                "cause": {"type": "string", "description": "One id from the cause list"},
                "hypothesis": {"type": "string", "description": "One short paragraph"},
                "scenario": {"type": "string", "description": "Oversold scenario YAML"},
            },
            "required": ["file", "cause", "hypothesis", "scenario"],
        },
    },
    {
        "name": "finish",
        "description": "End the trial with a short summary.",
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    },
]


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


class Model(Protocol):
    name: str

    def max_dollars(self, messages: list[dict], tools: list[dict]) -> float: ...

    def reply(self, messages: list[dict], tools: list[dict]) -> Reply: ...


@dataclass
class ScriptedModel:
    replies: list[Reply]
    name: str = "scripted"
    seen: list[list[dict]] = field(default_factory=list)

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


def model_scenario_format(text: str, terms: tuple[str, ...]) -> str:
    keep = []
    for line in text.splitlines():
        if line.startswith(HARNESS_ROWS) or any(term in line for term in terms):
            continue
        keep.append(line)
    return "\n".join(keep) + "\n"


def opening(root: Path, task_mode: str, issue: str | None, terms: tuple[str, ...]) -> list[dict]:
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
        "Scenario format:\n\n"
        + model_scenario_format((docs / "scenario-format.md").read_text(encoding="utf-8"), terms),
        "Check rules:\n\n" + (docs / "checks.md").read_text(encoding="utf-8"),
    ]
    return [
        {"role": "system", "content": (PROMPTS / "system.md").read_text(encoding="utf-8").strip()},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def counted_orders(snapshot: dict) -> int:
    return sum(
        1
        for o in snapshot.get("orders") or []
        if not o.get("canceled_at") and o.get("status") != "canceled"
    )


def level_text(sku: str, before: dict, after: dict) -> str:
    return (
        f"{sku} stock {before.get('stocked_quantity')} to {after.get('stocked_quantity')}, "
        f"reserved {before.get('reserved_quantity')} to {after.get('reserved_quantity')}"
    )


def run_summary(n: int, history: dict) -> str:
    calls = ", ".join(
        f"{a['id']} {a.get('outcome') or 'not sent'}"
        for a in (history.get("race") or {}).get("actions") or []
    )
    before = {lv["sku"]: lv for lv in (history.get("before") or {}).get("inventory_levels") or []}
    after = {lv["sku"]: lv for lv in (history.get("after") or {}).get("inventory_levels") or []}
    stock = "; ".join(level_text(sku, before[sku], after.get(sku, {})) for sku in sorted(before))
    failed = [v["check"] for v in history.get("verdicts") or [] if v["result"] == "fail"]
    unknown = " (counted inconclusive: a complete call ended with outcome unknown)"
    note = unknown if score.unknown_completion(history) else ""
    if history.get("harness_error"):
        note = " (the run could not be judged)"
    return (
        f"{n}. complete calls: {calls or 'none'}; "
        f"orders {counted_orders(history.get('after') or {})}; "
        f"{stock}; failed checks: {', '.join(failed) or 'none'}{note}"
    )


def history_feedback(number: int, histories: list[dict]) -> str:
    if not histories:
        return f"Attempt {number} was recorded but did not run."
    c = score.counts(histories)
    checks = ", ".join(
        f"{rule} failed in {row['fail']} of {len(histories)}" for rule, row in c.items()
    )
    lines = [
        f"Attempt {number} ran {len(histories)} times on Medusa {VERSION}.",
        f"Checks: {checks}. Inconclusive runs: {score.inconclusive_runs(histories)}.",
        "Runs:",
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
        self.ledger_path = score.ledger_path_for(self.root)
        self.folder = self.root / "runs" / "agent" / trial_id
        self.folder.mkdir(parents=True, exist_ok=False)
        self.transcript = self.folder / "transcript.jsonl"
        self.cases = score.load_cases(self.root / "benchmark" / "cases")
        self.causes = load_causes(self.root / "benchmark" / "causes.yaml")
        self.terms = forbidden_terms(self.root / "benchmark" / "cases")
        self.snapshot = Snapshot(
            self.root / "snapshots" / f"medusa-{VERSION}", READ_LINES, RESULT_CHARS
        )
        before = ledger.spent(ledger.load(self.ledger_path))["dollars"]
        self.budget = from_flags(self.caps.runs, self.caps.dollars or None, before)
        self.meter = Meter(self.ledger_path, self.budget, f"{trial_id}-model")
        self.messages = opening(self.root, task_mode, issue, self.terms)
        self.turns = 0
        self.attempts = 0
        self.tokens = [0, 0]
        self.end: str | None = None
        self.notes: dict[str, tuple[int, str]] = {}

    def log(self, event: dict) -> None:
        with self.transcript.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def shorten(self) -> None:
        for message in self.messages:
            if message["role"] != "tool":
                continue
            turn, note = self.notes[message["tool_call_id"]]
            if self.turns - turn >= self.keep_turns and message["content"] != note:
                message["content"] = note

    def tool_result(self, call: ToolCall, content: str, note: str) -> None:
        self.notes[call.id] = (self.turns, f"[{note}: removed after {self.keep_turns} turns]")
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
            if self.turns >= self.caps.turns:
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
            self.turns += 1
            self.tokens[0] += reply.input_tokens
            self.tokens[1] += reply.output_tokens
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
            self.log({"event": "reply", "turn": self.turns, "message": self.messages[-1]})
            if not reply.tool_calls:
                self.end = "the model stopped without calling finish"
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
            "input_tokens": self.tokens[0],
            "output_tokens": self.tokens[1],
            "timestamp": now(),
        }
        ledger.append(self.ledger_path, summary)
        self.log({"event": "end", **summary})
        return summary

    def call_model(self) -> Reply:
        cap = self.model.max_dollars(self.messages, TOOLS)

        def call():
            reply = self.model.reply(self.messages, TOOLS)
            usage = Usage(self.model.name, reply.input_tokens, reply.output_tokens, reply.dollars)
            return reply, usage

        return self.meter.paid_call(self.model.name, cap, call)

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
                self.tool_result(call, self.submit(args), f"submit_attempt {self.attempts}")
                if self.end is None and self.attempts >= self.caps.attempts:
                    self.end = f"attempt cap: {self.caps.attempts} attempts"
            elif call.name == "finish":
                self.tool_result(call, "Trial finished.", "finish")
                self.end = "finished by the model"
                self.log({"event": "finish", "summary": args.get("summary")})
            else:
                self.tool_result(call, f"error: no tool named {call.name!r}", call.name)
        except ToolError as err:
            self.tool_result(call, f"error: {err}", f"{call.name} error")

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
                "cause": self.safe(args.get("cause")),
                "hypothesis": self.safe(args.get("hypothesis")),
                "scenario_sha256": None,
                "refused": reason,
                "timestamp": now(),
            },
        )
        return f"Attempt {number} refused: {reason}"

    def submit(self, args: dict) -> str:
        self.attempts += 1
        number = self.attempts
        file, cause = args.get("file"), args.get("cause")
        hypothesis, text = args.get("hypothesis"), args.get("scenario")
        if not (isinstance(file, str) and file.startswith("packages/")):
            return self.refuse(number, args, "file must be one source path under packages/")
        if cause not in self.causes:
            return self.refuse(number, args, "cause must be one id from the cause list")
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
            return f"Attempt {number} was not run: the run cap was reached."
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
            return f"Attempt {number} recorded."
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
    run = sub.add_parser("run", help="run one trial with a scripted model")
    run.add_argument("--script", required=True, help="JSON list of scripted replies")
    run.add_argument("--task-mode", choices=ledger.TASK_MODES, required=True)
    run.add_argument("--issue", help="case whose issue the guided mode shows")
    run.add_argument("--feedback", choices=ledger.FEEDBACK_MODES, required=True)
    run.add_argument("--dollar-cap", type=float, default=0.0)
    est = sub.add_parser("estimate", help="estimate tokens for one trial")
    est.add_argument("--issue", default="medusa-16502-lines")
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "estimate":
        print(json.dumps(estimate_trial(root, args.issue), indent=2))
        return 0
    items = json.loads(Path(args.script).read_text(encoding="utf-8"))
    model = ScriptedModel.from_json(items)
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
        caps=Caps(dollars=args.dollar_cap),
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
