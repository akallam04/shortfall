import datetime
from pathlib import Path

from shortfall.answers import grade
from shortfall.score import REPRODUCED, VIOLATION, load_cases


def _time(stamp: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(stamp)


def plain_failed_rules(final: dict) -> dict[str, int]:
    v = final.get("violation") or {}
    return {rule: n for rule, n in (v.get("rules") or {}).items() if n}


def backed(final: dict | None) -> bool:
    return bool(final) and (final.get("violation") or {}).get("result") == VIOLATION


def score_trial(root: Path, records: list[dict]) -> dict:
    cases = load_cases(Path(root) / "benchmark" / "cases")
    trial = next(r for r in records if r.get("kind") == "agent-trial")
    end = next((r for r in records if r.get("kind") == "agent-end"), None)
    run_id = trial["trial_id"]
    preds = sorted(
        (r for r in records if r.get("kind") == "prediction"), key=lambda r: r["attempt"]
    )
    finals = {r["attempt_id"]: r for r in records if r.get("kind") == "final"}
    attempts = []
    expected_hits = expected_total = 0
    for p in preds:
        final = finals.get(p["attempt_id"])
        failed = plain_failed_rules(final) if final else {}
        expected = p.get("expected_check")
        hit = None
        if p.get("refused") is None and final and expected:
            hit = (not failed) if expected == "none" else expected in failed
            expected_total += 1
            expected_hits += hit
        attempts.append(
            {
                "attempt": p["attempt"],
                "file": p.get("file"),
                "cause": p.get("cause"),
                "expected_check": expected,
                "refused": p.get("refused"),
                "ran": final is not None,
                "violation": (final or {}).get("violation"),
                "plain_failed_rules": failed,
                "expected_check_failed": hit,
                "reproduced": ((final or {}).get("reproduced") or {}).get("cases"),
                "located": (final or {}).get("located"),
                "manual_check": (final or {}).get("manual_check") or [],
                "stop_reason": (final or {}).get("stop_reason"),
                "oversold_runs": (final or {}).get("oversold_runs"),
            }
        )
    per_case = {}
    for case_id in sorted(cases):
        first = None
        for p in preds:
            final = finals.get(p["attempt_id"])
            if not final:
                continue
            if ((final.get("reproduced") or {}).get("cases") or {}).get(case_id) != REPRODUCED:
                continue
            graded = ((final.get("located") or {}).get("cases") or {}).get(case_id) or {}
            run = (final.get("reproduced_at") or {}).get(case_id)
            if first is None or (run is not None and run < first["runs_to_first"]):
                first = {
                    "attempt": p["attempt"],
                    "runs_to_first": run,
                    "file": p.get("file"),
                    "cause": p.get("cause"),
                    "file_grade": graded.get("file"),
                    "cause_grade": graded.get("cause"),
                }
        per_case[case_id] = {"reproduced": first is not None, **(first or {})}
    by_attempt = {p["attempt"]: p for p in preds}
    claims = []
    for c in (end or {}).get("claims") or []:
        p = by_attempt.get(c["attempt"])
        final = finals.get(p["attempt_id"]) if p else None
        if p is None or p.get("refused") is not None:
            why = "refused"
        elif final is None:
            why = "never ran"
        elif backed(final):
            why = "violation on plain Medusa"
        else:
            why = "no violation"
        claims.append(
            {
                **c,
                "backed": why == "violation on plain Medusa",
                "why": why,
                "grades": {
                    case_id: {
                        k: v
                        for k, v in grade(info.folder, c["file"], c.get("cause")).items()
                        if k in ("file", "cause")
                    }
                    for case_id, info in sorted(cases.items())
                },
            }
        )
    calls = [
        r
        for r in records
        if r.get("kind") == "spend"
        and r.get("item") == "paid_call"
        and r.get("state") == "settled"
        and r["attempt_id"] == f"{run_id}-model"
    ]
    prompts = [
        (r.get("input_tokens") or 0)
        + (r.get("cache_write_tokens") or 0)
        + (r.get("cache_read_tokens") or 0)
        for r in calls
    ]
    wall = None
    if end:
        wall = round((_time(end["timestamp"]) - _time(trial["timestamp"])).total_seconds())
    return {
        "trial_id": run_id,
        "task_mode": trial["task_mode"],
        "feedback": trial["feedback"],
        "issue": trial.get("issue"),
        "model": trial["model"],
        "sdk_version": trial.get("sdk_version"),
        "knowledge_cutoff": trial.get("knowledge_cutoff"),
        "caps": {
            "runs": trial["run_cap"],
            "attempts": trial["attempt_cap"],
            "turns": trial["turn_cap"],
            "dollars": trial["dollar_cap"],
        },
        "end_reason": (end or {}).get("reason"),
        "finished_by_model": (end or {}).get("reason") == "finished by the model",
        "turns": (end or {}).get("turns"),
        "attempts": len(preds),
        "refused": sum(1 for p in preds if p.get("refused") is not None),
        "oversold_runs": (end or {}).get("oversold_runs"),
        "cases": per_case,
        "cases_reproduced": sum(1 for c in per_case.values() if c["reproduced"]),
        "claims": claims if end and end.get("claims") is not None else None,
        "claims_backed": sum(1 for c in claims if c["backed"]),
        "claims_unbacked": sum(1 for c in claims if not c["backed"]),
        "expected_check": {"hits": expected_hits, "of": expected_total},
        "manual_check": [n for a in attempts for n in a["manual_check"]],
        "tokens": {
            "input": (end or {}).get("input_tokens"),
            "cache_write": (end or {}).get("cache_write_tokens"),
            "cache_read": (end or {}).get("cache_read_tokens"),
            "output": (end or {}).get("output_tokens"),
        },
        "model_calls": len(calls),
        "largest_prompt_tokens": max(prompts) if prompts else 0,
        **(
            {"gate_answers": end["gate_answers"]}
            if (end or {}).get("gate_answers") is not None
            else {}
        ),
        "dollars": (end or {}).get("dollars"),
        "wall_seconds": wall,
        "attempt_list": attempts,
    }
