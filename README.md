# Shortfall

Shortfall is an AI agent that looks for race bugs in open-source commerce engines. It reads an engine's code, guesses where concurrent requests could break a stock or order rule, and writes an [Oversold](https://github.com/akallam04/oversold) scenario to test each guess. It reports a bug only when Oversold reproduces it on a local copy of the engine.

It is graded on a benchmark of real bugs that are already public, against simple baselines that use no model.

## Status

Setting up. No results yet.

## How it uses Oversold

Shortfall runs Oversold only through its command line, from a clone pinned to one public commit in `oversold.lock`. `make oversold` clones that commit into `.oversold/`, checks it, builds it and makes the clone read-only.

Oversold runs on Shortfall's own Docker engine, a [Colima](https://github.com/abiosoft/colima) VM named `shortfall` that can see only this folder, so every image a run uses was built from the pinned clone. `make engine-up` starts it and `make engine-down` stops it. `scripts/oversold.sh` is the only way Shortfall runs Oversold: it checks the pin, sends every run to that engine and writes run folders to `runs/`.

## Safety

Shortfall only runs engines on local copies that Oversold starts in Docker, never on live stores or anyone's servers. A bug that no public issue already covers is reported privately to that project first.

## License

MIT. See [LICENSE](LICENSE).
