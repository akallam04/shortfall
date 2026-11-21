import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from shortfall import trials

OVERSOLD_UP = ["sh", "scripts/oversold.sh", "up"]


def launch(
    root: Path,
    plan_arg: str,
    raise_cap: float = 0.0,
    run: Callable = subprocess.run,
    popen: Callable = subprocess.Popen,
    which: Callable = shutil.which,
) -> int:
    plan_path = Path(plan_arg).resolve()
    plan = trials.load_plan(root, plan_path)
    state = trials.State(root, plan)
    if state.pid_path.exists():
        text = state.pid_path.read_text().strip()
        if text.isdigit() and trials.pid_alive(int(text)):
            print(f"plan {plan.name} is already running as process {text}")
            return 1
    up = run(OVERSOLD_UP, cwd=root)
    if up.returncode != 0:
        print(f"sh scripts/oversold.sh up failed with exit code {up.returncode}, plan not started")
        return 1
    rel = os.path.relpath(plan_path, Path(root).resolve())
    cmd = [sys.executable, "-u", "-m", "shortfall.trials", rel]
    if raise_cap:
        cmd += ["--raise-dollar-cap", str(raise_cap)]
    log = state.pid_path.with_suffix(".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "ab") as out:
        proc = popen(
            cmd,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    state.pid_path.write_text(f"{proc.pid}\n")
    if which("caffeinate"):
        popen(
            ["caffeinate", "-ims", "-w", str(proc.pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    print(f"plan {plan.name} started as process {proc.pid}, log {log.relative_to(root)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.launch")
    p.add_argument("plan")
    p.add_argument("--raise-dollar-cap", type=float, default=0.0)
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    return launch(root, args.plan, args.raise_dollar_cap)


if __name__ == "__main__":
    sys.exit(main())
