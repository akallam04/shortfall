from dataclasses import dataclass

DEFAULT_SESSION_RUNS = 600
DEFAULT_ATTEMPT_RUNS = 25
DEFAULT_DOLLARS = 0.0

SESSION = "session runs"
ATTEMPT = "attempt runs"
DOLLARS = "dollars"


class CapReached(Exception):
    def __init__(self, cap: str, used: float, limit: float, asked: float):
        self.cap = cap
        self.used = used
        self.limit = limit
        self.asked = asked
        super().__init__(f"{cap} cap reached: used {used:g} of {limit:g}, asked for {asked:g} more")


@dataclass
class Budget:
    session_runs: int = DEFAULT_SESSION_RUNS
    attempt_runs: int = DEFAULT_ATTEMPT_RUNS
    dollars: float = DEFAULT_DOLLARS
    session_used: int = 0
    attempt_used: int = 0
    dollars_used: float = 0.0
    attempts: int = 0

    def __post_init__(self):
        for name in ("session_runs", "attempt_runs"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a whole number, 0 or more")
        if not isinstance(self.dollars, int | float) or self.dollars < 0:
            raise ValueError("dollars must be 0 or more")

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

    def charge_dollars(self, amount: float) -> None:
        if not isinstance(amount, int | float) or amount < 0:
            raise ValueError("dollars to charge must be 0 or more")
        if self.dollars_used + amount > self.dollars:
            raise CapReached(DOLLARS, self.dollars_used, self.dollars, amount)
        self.dollars_used += amount

    def usage(self) -> dict:
        return {
            SESSION: {"used": self.session_used, "cap": self.session_runs},
            ATTEMPT: {"last attempt used": self.attempt_used, "cap": self.attempt_runs},
            DOLLARS: {"used": self.dollars_used, "cap": self.dollars},
            "attempts": self.attempts,
        }

    def describe(self) -> str:
        return "\n".join(
            [
                f"session runs: used {self.session_used} of {self.session_runs}",
                f"attempt runs: last attempt used {self.attempt_used} of {self.attempt_runs}",
                f"dollars: used {self.dollars_used:.2f} of {self.dollars:.2f}",
                f"attempts: {self.attempts}",
            ]
        )


def from_flags(max_runs: int | None = None, raise_dollar_cap: float | None = None) -> Budget:
    session = DEFAULT_SESSION_RUNS if max_runs is None else max_runs
    dollars = DEFAULT_DOLLARS if raise_dollar_cap is None else raise_dollar_cap
    return Budget(session_runs=session, attempt_runs=DEFAULT_ATTEMPT_RUNS, dollars=dollars)
