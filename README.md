# Shortfall

Shortfall looks for a kind of bug in online shop software that only shows up when several customers act at the same moment. It uses an AI model to guess where these bugs hide, and it tests every guess on a private copy of the shop running on one computer.

## The problem, in everyday terms

A shop has one item left, and two people press Buy at the same moment. A correct shop sells the item once and tells the second person it is sold out. Some shops sell it twice, because both purchases check the stock before either one has taken the item. The shop then owes someone an item it does not have.

## What Shortfall does

1. It reads the code of an open-source shop engine called Medusa.
2. It guesses where purchases made at the same moment could break a rule, such as "never sell more than you have".
3. It writes a small test for that guess: which items are in stock, how many shoppers there are, and when they press Buy.
4. It runs the test many times on a private copy of the shop on this computer.
5. It counts a bug only if the test shows the rule breaking, and a copy of the shop with the public fix for that bug passes the same test.

## What has been measured so far

A run is one go of a test: a fresh copy of the shop starts, the shoppers press Buy, and the result is checked against the rules.

The benchmark has three test scenarios built from two real Medusa bugs that were already public. Each was run 30 times on plain Medusa 2.22.0 and 30 times on a copy with the public fix.

| Test scenario | Public bug | Rule broken on plain Medusa | Rule broken with the fix |
|---|---|---|---|
| The last unit is sold twice | [#17032](https://github.com/medusajs/medusa/issues/17032) | 23 of 30 runs | 0 of 30 runs ([fix #17420](https://github.com/medusajs/medusa/pull/17420)) |
| The count of reserved stock goes wrong | [#17032](https://github.com/medusajs/medusa/issues/17032) | 30 of 30 runs | 0 of 30 runs ([fix #17420](https://github.com/medusajs/medusa/pull/17420)) |
| Two cart lines that use the same stock are oversold | [#16502](https://github.com/medusajs/medusa/issues/16502) | 30 of 30 runs | 0 of 30 runs ([fix #16961](https://github.com/medusajs/medusa/pull/16961)) |

Two simple methods that use no AI were measured for comparison, each in 3 trials of at most 300 runs:

- A fixed list of test shapes found all three scenarios in 3 of 3 trials.
- Randomly drawn tests found the two #17032 scenarios in 3 of 3 trials and the #16502 scenario in 1 of 3.

## What is not done yet

The AI agent is built and has been tested with a scripted stand-in, but it has not run with a real AI model. No results for it exist yet.

## Why you can trust the numbers

- Every run is saved in this repo with its full record, and every result is recomputed from those records automatically on each change.
- The benchmark uses two real bugs that were already public, turned into three test scenarios.
- Every test runs on private copies of the shop on one computer, never on live shops or anyone's servers.

## Glossary

- **Run**: one go of a test on a fresh copy of the shop, checked against the rules afterwards.
- **Scenario**: the small test file that says which items are in stock, which shoppers there are and when they press Buy.
- **Check**: a rule the shop must keep, checked after every run, such as "never sell more than the stock".
- **Control**: the same scenario run on a fix build, to show that a failure comes from that bug and not from something else.
- **Fix build**: a copy of Medusa with the public fix for one bug applied.
- **Baseline**: a simple method that uses no AI, measured the same way as the agent so its results can be compared.

## How it uses Oversold

Shortfall runs every test through [Oversold](https://github.com/akallam04/oversold), a separate tool that starts Medusa in Docker, sends the requests a scenario describes and checks the rules. Shortfall uses only Oversold's command line, from a clone pinned to one public commit in `oversold.lock`. `make oversold` clones that commit into `.oversold/`, checks it, builds it and makes the clone read-only.

## The engine

Oversold runs on Shortfall's own Docker engine, a [Colima](https://github.com/abiosoft/colima) VM named `shortfall` that can see only this folder. Every image a run uses comes from the pinned clone: the Medusa images it builds and the public base images its Compose file and Dockerfile name. `scripts/oversold.sh` is the only way Shortfall runs Oversold. It checks the pin, sends every run to that engine and writes run folders to `runs/`.

## How to run

```bash
make venv PYTHON=python3.14
```

```bash
make oversold
```

```bash
make test
```

```bash
make lint
```

Runs on Medusa need the engine and Oversold's Postgres:

```bash
make engine-up
```

```bash
sh scripts/oversold.sh up
```

When the runs are done, stop them in the reverse order:

```bash
sh scripts/oversold.sh down
```

```bash
make engine-down
```

## The agent

`src/shortfall/agent.py` runs one trial of the agent. The model can list, read and search the Medusa 2.22.0 source, submit an attempt (a file, a cause from a fixed list, a short hypothesis and a scenario) and finish. Each attempt and its prediction go into `runs/ledger.jsonl` before its first run, and each is scored the same way as the baselines. A trial stops at 300 runs, 12 attempts, 60 model turns or a dollar cap. In the `none` feedback mode the model only learns that an attempt was recorded. In the `history` mode it also sees, for the runs on plain Medusa only, how often each check failed and a short summary of each run. It never sees control runs, the benchmark cases or their answers. The prompts are in `src/shortfall/prompts/`. Only a scripted stand-in model is wired up so far.

## Benchmark

Each folder in [benchmark/cases/](benchmark/cases/) is one public bug. `case.yaml` names the issue, the rule it breaks, the Medusa versions, the controls and what the agent may see. `reference.yaml` is a scenario written by hand that reproduces it. `results/` holds every measured run with its full history, gzipped, so `oversold check --verify` can recompute every verdict. [benchmark/README.md](benchmark/README.md) has the measured results, the scoring rules and the baselines.

## Safety

Shortfall only runs engines on local copies that Oversold starts in Docker, never on live stores or anyone's servers. A bug that no public issue already covers is reported privately to that project first.

## License

MIT. See [LICENSE](LICENSE).
