from dataclasses import dataclass

DEFAULT_SESSION_RUNS = 600
DEFAULT_ATTEMPT_RUNS = 25
DEFAULT_DOLLARS = 0.0
TOTAL_DOLLAR_CAP = 20.0

SESSION = "session runs"
ATTEMPT = "attempt runs"
DOLLARS = "session dollars"
TOTAL_DOLLARS = "total dollars"

_EPSILON = 1e-9


class CapReached(Exception):
    def __init__(self, cap: str, used: float, limit: float, asked: float):
        self.cap = cap
        self.used = used
        self.limit = limit
        self.asked = asked
        super().__init__(f"{cap} cap reached: used {used:g} of {limit:g}, asked for {asked:g} more")


def _is_amount(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0


@dataclass
class Budget:
    session_runs: int = DEFAULT_SESSION_RUNS
    attempt_runs: int = DEFAULT_ATTEMPT_RUNS
    dollars: float = DEFAULT_DOLLARS
    total_dollar_cap: float = TOTAL_DOLLAR_CAP
    dollars_before: float = 0.0
    session_used: int = 0
    attempt_used: int = 0
    dollars_used: float = 0.0
    dollars_reserved: float = 0.0
    attempts: int = 0

    def __post_init__(self):
        for name in ("session_runs", "attempt_runs"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a whole number, 0 or more")
        for name in ("dollars", "total_dollar_cap", "dollars_before"):
            if not _is_amount(getattr(self, name)):
                raise ValueError(f"{name} must be 0 or more")
        if self.total_dollar_cap > TOTAL_DOLLAR_CAP:
            raise ValueError(f"the total dollar cap cannot be above {TOTAL_DOLLAR_CAP:.2f}")

    def start_attempt(self) -> None:
        self.attempt_used = 0
        self.attempts += 1

    def session_left(self) -> int:
        return self.session_runs - self.session_used

    def attempt_left(self) -> int:
        return self.attempt_runs - self.attempt_used

    def charge_runs(self, n: int) -> None:
        if type(n) is not int or n <= 0:
            raise ValueError("runs to charge must be a whole number above 0")
        if self.session_used + n > self.session_runs:
            raise CapReached(SESSION, self.session_used, self.session_runs, n)
        if self.attempt_used + n > self.attempt_runs:
            raise CapReached(ATTEMPT, self.attempt_used, self.attempt_runs, n)
        self.session_used += n
        self.attempt_used += n

    def session_dollars(self) -> float:
        return self.dollars_used + self.dollars_reserved

    def total_dollars(self) -> float:
        return self.dollars_before + self.session_dollars()

    def reserve_dollars(self, amount: float) -> None:
        if not _is_amount(amount) or amount == 0:
            raise ValueError("dollars to reserve must be above 0")
        if self.session_dollars() + amount > self.dollars + _EPSILON:
            raise CapReached(DOLLARS, self.session_dollars(), self.dollars, amount)
        if self.total_dollars() + amount > self.total_dollar_cap + _EPSILON:
            raise CapReached(TOTAL_DOLLARS, self.total_dollars(), self.total_dollar_cap, amount)
        self.dollars_reserved += amount

    def settle_dollars(self, reserved: float, actual: float) -> None:
        if not _is_amount(reserved) or not _is_amount(actual):
            raise ValueError("dollars to settle must be 0 or more")
        if reserved > self.dollars_reserved + _EPSILON:
            raise ValueError("cannot settle more than is reserved")
        self.dollars_reserved = max(self.dollars_reserved - reserved, 0.0)
        self.dollars_used += actual

    def charge_dollars(self, amount: float) -> None:
        if not _is_amount(amount):
            raise ValueError("dollars to charge must be 0 or more")
        if amount == 0:
            return
        self.reserve_dollars(amount)
        self.settle_dollars(amount, amount)

    def usage(self) -> dict:
        return {
            SESSION: {"used": self.session_used, "cap": self.session_runs},
            ATTEMPT: {"last attempt used": self.attempt_used, "cap": self.attempt_runs},
            DOLLARS: {
                "used": self.dollars_used,
                "reserved": self.dollars_reserved,
                "cap": self.dollars,
            },
            TOTAL_DOLLARS: {
                "before this session": self.dollars_before,
                "total": self.total_dollars(),
                "cap": self.total_dollar_cap,
            },
            "attempts": self.attempts,
        }

    def describe(self) -> str:
        reserved = (
            f", {self.dollars_reserved:.2f} reserved and not settled"
            if self.dollars_reserved
            else ""
        )
        return "\n".join(
            [
                f"session runs: used {self.session_used} of {self.session_runs}",
                f"attempt runs: last attempt used {self.attempt_used} of {self.attempt_runs}",
                f"dollars this session: used {self.dollars_used:.2f} of {self.dollars:.2f}"
                f"{reserved}",
                f"dollars across all sessions: {self.total_dollars():.2f} of "
                f"{self.total_dollar_cap:.2f}",
                f"attempts: {self.attempts}",
            ]
        )


def from_flags(
    max_runs: int | None = None,
    raise_dollar_cap: float | None = None,
    dollars_before: float = 0.0,
) -> Budget:
    session = DEFAULT_SESSION_RUNS if max_runs is None else max_runs
    dollars = DEFAULT_DOLLARS if raise_dollar_cap is None else raise_dollar_cap
    return Budget(
        session_runs=session,
        attempt_runs=DEFAULT_ATTEMPT_RUNS,
        dollars=dollars,
        dollars_before=dollars_before,
    )
