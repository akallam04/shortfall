# Shortfall

Shortfall is an AI agent that looks for race bugs in open-source commerce engines. It reads an engine's code, guesses where concurrent requests could break a stock or order rule, and writes an [Oversold](https://github.com/akallam04/oversold) scenario to test each guess. It reports a bug only when Oversold reproduces it on a local copy of the engine.

It is graded on a benchmark of real bugs that are already public, against simple baselines that use no model.

## Status

Three benchmark cases from public Medusa issues, each reproduced by hand with Oversold on Medusa 2.21.2 and 2.19.0, two of them with a one-server control that held in 30 of 30 runs. No agent yet. See [benchmark/README.md](benchmark/README.md).

## How it uses Oversold

Shortfall runs Oversold only through its command line, from a clone pinned to one public commit in `oversold.lock`. `make oversold` clones that commit into `.oversold/`, checks it, builds it and makes the clone read-only.

Oversold runs on Shortfall's own Docker engine, a [Colima](https://github.com/abiosoft/colima) VM named `shortfall` that can see only this folder. Every image a run uses comes from the pinned clone: the Medusa images it builds and the public base images its Compose file and Dockerfile name. `make engine-up` starts the engine and `make engine-down` stops it. `scripts/oversold.sh` is the only way Shortfall runs Oversold: it checks the pin, sends every run to that engine and writes run folders to `runs/`. `sh scripts/oversold.sh up` starts Oversold's stack in the engine before runs, and `sh scripts/oversold.sh down` removes it.

## Benchmark

Each folder in [benchmark/cases/](benchmark/cases/) is one public bug. `case.yaml` names the issue, the rule it breaks, the Medusa versions, the control and what the agent may see. `reference.yaml` is a scenario written by hand that reproduces it. The first three come from Oversold's own scenarios. `results/` holds every measured run with its full history, gzipped, so `oversold check --verify` can recompute every verdict. [benchmark/README.md](benchmark/README.md) has the measured results.

## Safety

Shortfall only runs engines on local copies that Oversold starts in Docker, never on live stores or anyone's servers. A bug that no public issue already covers is reported privately to that project first.

## License

MIT. See [LICENSE](LICENSE).
