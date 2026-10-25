import datetime
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shortfall import ledger
from shortfall.budget import Budget


@dataclass(frozen=True)
class Usage:
    model: str
    input_tokens: int
    output_tokens: int
    dollars: float


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


class Meter:
    def __init__(self, path: str | Path, budget: Budget, attempt_id: str):
        self.path = Path(path)
        self.budget = budget
        self.attempt_id = attempt_id
        self.spends = 0
        self.dollars = 0.0

    def _spend_id(self) -> str:
        self.spends += 1
        return f"{self.attempt_id}-s{self.spends:02d}"

    def _spend(self, **fields) -> None:
        record = {
            "kind": "spend",
            "attempt_id": self.attempt_id,
            "set": None,
            "oversold_runs": None,
            "model": None,
            "input_tokens": None,
            "output_tokens": None,
            "dollars": 0,
        }
        record.update(fields)
        record["timestamp"] = now()
        ledger.append(self.path, record)

    def start(self, fields: dict) -> None:
        record = {"kind": "started", "attempt_id": self.attempt_id, **fields, "timestamp": now()}
        ledger.append(self.path, record)

    def runs(self, set_name: str, n: int) -> None:
        self.budget.charge_runs(n)
        self._spend(
            spend_id=self._spend_id(),
            item="oversold_runs",
            state="charged",
            set=set_name,
            oversold_runs=n,
        )

    def paid_call(self, model: str, max_dollars: float, call: Callable[[], tuple[Any, Usage]]):
        self.budget.reserve_dollars(max_dollars)
        spend_id = self._spend_id()
        self._spend(
            spend_id=spend_id, item="paid_call", state="reserved", model=model, dollars=max_dollars
        )
        result, usage = call()
        self.budget.settle_dollars(max_dollars, usage.dollars)
        self.dollars += usage.dollars
        self._spend(
            spend_id=spend_id,
            item="paid_call",
            state="settled",
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            dollars=usage.dollars,
        )
        if usage.dollars > max_dollars:
            raise RuntimeError(
                f"paid call cost {usage.dollars:.4f} dollars, above its reservation of "
                f"{max_dollars:.4f}"
            )
        return result

    def finish(self, entry: dict) -> None:
        entry["kind"] = "final"
        entry["dollars"] = round(self.dollars, 6)
        ledger.append(self.path, entry)
