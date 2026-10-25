# Benchmark

Each case is one public bug in an open-source commerce engine that [Oversold](https://github.com/akallam04/oversold) can reproduce on a local copy. The benchmark grades whether Shortfall can find it.

## A case

A case is a folder in [cases/](cases/) named after its id.

- `case.yaml`: what the case is.
- `reference.yaml`: an Oversold scenario written by hand that reproduces the bug.
- `control.yaml`: the control scenario, for cases with a one-server control.
- `results/<version>-reference/` and `results/<version>-control/`: the measured runs, exported with `oversold export`: the scenario, `report.json`, `report.md` and every run's history, gzipped.

Fields in `case.yaml`:

| Field | Meaning |
|---|---|
| `schema` | Always `shortfall.case/v1`. |
| `id` | Kebab-case id, equal to the folder name. |
| `title` | One line describing the bug. |
| `engine` | The engine, `medusa`. |
| `versions` | The engine versions the case runs on, like `2.21.2`. |
| `issue.url` | The public GitHub issue for the bug. |
| `issue.opened` | The date the issue was opened. |
| `issue.state` | The issue's state when the case was added. |
| `rule` | The Oversold check the bug breaks: `no_oversell`, `reserved_matches_reservations`, `one_order_per_cart` or `no_orphaned_orders`. |
| `control.kind` | `one-server`, `fixed-version` or `none`. |
| `control.version` | With `fixed-version` only: a version where the bug is fixed. |
| `control.reason` | With `none` only: why the case has no control. |
| `reference.file` | The reference scenario's file in the folder. |
| `reference.source` | Where the reference scenario comes from. |
| `agent_sees.guided` | What the agent may read in the guided setting. |
| `agent_sees.unguided` | What the agent may read in the unguided setting. |
| `notes` | Optional notes. |

`load_case` in `src/shortfall/cases.py` reads a case strictly: an unknown field at any level is an error.

## Controls

A control is a scenario that should not fail the case's rule, so a failure in the reference comes from the bug and not from the scenario.

- `one-server`: the reference runs on two servers, and the control is the same scenario on one server. `python -m shortfall.control reference.yaml` writes it: every server field becomes 1, the name gets `-control` and the description says what it is. Everything else stays the same.
- `fixed-version`: the same scenario on a version where the bug is fixed.
- `none`: no control yet, with the reason in `control.reason`.

An agent's scenario will count as finding a case when the case's rule fails in at least 1 of 10 runs on the case's version and in 0 of 10 runs of its control. Reference runs use 30.

## Results

Each row is one set of 30 runs. "Rule failed" counts the runs where the case's rule failed. "Other checks failed" lists every other check that failed, with its number of failed runs.

| Case | Version | Set | Rule failed | Other checks failed | Inconclusive runs | Report |
|---|---|---|---|---|---|---|
| medusa-17032-last-unit | 2.21.2 | reference | 20 of 30 | reserved_matches_reservations 20 | 0 | [report](cases/medusa-17032-last-unit/results/2.21.2-reference/report.md) |
| medusa-17032-last-unit | 2.21.2 | control | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/2.21.2-control/report.md) |
| medusa-17032-last-unit | 2.19.0 | reference | 25 of 30 | reserved_matches_reservations 25 | 0 | [report](cases/medusa-17032-last-unit/results/2.19.0-reference/report.md) |
| medusa-17032-last-unit | 2.19.0 | control | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/2.19.0-control/report.md) |
| medusa-17032-counter | 2.21.2 | reference | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2.21.2-reference/report.md) |
| medusa-17032-counter | 2.21.2 | control | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2.21.2-control/report.md) |
| medusa-17032-counter | 2.19.0 | reference | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2.19.0-reference/report.md) |
| medusa-17032-counter | 2.19.0 | control | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2.19.0-control/report.md) |
| medusa-16502-lines | 2.21.2 | reference | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/2.21.2-reference/report.md) |
| medusa-16502-lines | 2.19.0 | reference | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/2.19.0-reference/report.md) |

A case is reproduced on a version when its rule failed in at least one reference run and in no control run. A case with no control is "reproduced, no control yet".

| Case | 2.21.2 | 2.19.0 |
|---|---|---|
| medusa-17032-last-unit | reproduced | reproduced |
| medusa-17032-counter | reproduced | reproduced |
| medusa-16502-lines | reproduced, no control yet | reproduced, no control yet |

## Setup

- Oversold at commit `a18d5c9f3892dbca86effa0766e975985f8324bd`, from `oversold.lock`.
- Colima 0.10.3, profile `shortfall`: 4 CPUs, 6 GiB memory, 40 GiB disk, `vz` VM, `virtiofs` mount of this repo, read-only.
- Docker client 29.8.2.
- macOS 27.0.1 on Apple silicon.
- `oversold-medusa:2.21.2`: `sha256:8b684bf5b7c6af1b401200325dc4ff285f96bdf8c44e0a68f42b2408d77e0796`
- `oversold-medusa:2.19.0`: `sha256:170f4d29b9d544cdf96e06f7a75d4d3306f28abd80024cfdbe46044c0096e112`
- `postgres:15.19-alpine`: image `sha256:d2c2ced0372e855e4c257a9e9b5725f403847c01cfb64facbf2b21dbdadb2d74`, digest `postgres@sha256:d2c2ced0372e855e4c257a9e9b5725f403847c01cfb64facbf2b21dbdadb2d74`
- Runs from 2026-10-22 06:28:45 UTC to 2026-10-22 06:59:12 UTC.

Every history records the Medusa image ID of each server and the Oversold commit. All 300 match the images above and the pin, with no local changes.

Run sets from different sessions are comparable only when the Medusa image ID matches. `sh scripts/oversold.sh up` builds the image for the version in `.oversold/.env` only when it is missing and otherwise starts the existing one, and it prints the image ID and digest every time. `sh scripts/oversold.sh up --rebuild` forces a build, which gives a new image ID.

## Baseline sweep

`python -m shortfall.sweep` is a baseline that uses no model. It writes candidate scenario files from a fixed parameter space and scores each one through the pinned Oversold. It uses only fields the scenario format already has: the three seeded SKUs, cart count, lines per cart and their quantities, starting stock, server count and completion order. The generator in `src/shortfall/sweep.py` does not read the cases, their reference files or their controls. Only the scoring step in `src/shortfall/score.py` maps a result to a case.

Candidates go in `runs/sweep/<UTC time>/`. Both modes give the same files in the same order for the same `--seed`.

- `--mode grid` walks 32 candidates in this order: 2 servers, then 1. Within each, carts holding OVS-SOLO 1, then OVS-PIECE 1, then OVS-PIECE 1 and OVS-TWOPACK 1. Within each, 2 carts, then 10, split evenly across the servers. Within each, stock `under` (only for the two-line carts), `short`, then `ample`, all completions released together. Then 4 candidates released one after another, with 2 carts and `short` stock: 2 servers with OVS-SOLO 1, 2 servers with OVS-PIECE 1 and OVS-TWOPACK 1, then the same two on 1 server.
- Stock levels, per inventory item: `under` is one cart's need minus 1, `short` is the total need minus one cart's need, and `ample` is 10 times the total need.
- `under` is used only for carts with more than one line. Medusa will not add a line to a cart when the stock is below that line's quantity, so a one-line cart with `under` stock can never be prepared. With two lines on the same item, each line still fits on its own while the cart as a whole does not, which is the shape behind #16502. The grid checks that every line fits the stock on its own.
- `--mode random --count N` samples N candidates from the same space with up to two cart groups, quantities from 1 to 3 and random stock and release.

### Scoring

1. Screen: run the candidate once, then 2 more times. If any screen run fails while preparing a cart, the verdict is `unpreparable` and the rest of the screen is skipped. This applies to every candidate, from the sweep or from an agent. Otherwise, if no check fails in the 3 runs, the verdict is `no match`.
2. Score: run the candidate 10 times. For a two-server candidate, generate its one-server control with `python -m shortfall.control` and run that 10 times.
3. A candidate matches a case when the case's rule failed in at least 1 of the 10 candidate runs and in 0 of the 10 control runs, with no inconclusive control run.
4. A one-server candidate has no one-server control, so a rule failure there is `reproduction only`, never a match. `medusa-16502-lines` has no control yet either.
5. A result that cannot be decided because runs were inconclusive is `inconclusive`. Inconclusive runs count against the caps like any other run, and so does the run that shows a candidate is `unpreparable`. The sweep stops when 3 attempts in a row have only inconclusive runs, not counting `unpreparable` ones.

A candidate is mapped to a case by the case's rule and the server count of the case's reference scenario:

| Rule that failed | Candidate servers | Case |
|---|---|---|
| `no_oversell` | 2 | medusa-17032-last-unit |
| `reserved_matches_reservations` | 2 | medusa-17032-counter |
| `no_oversell` | 1 | medusa-16502-lines |

A two-server candidate can match both two-server cases when both rules fail on it and on neither in its control.

### Failures outside the public issues

Every failed check in every set is compared with this map of public issues. A failure the map does not cover stops the sweep at once, and nothing about it is pushed.

| Rule | Shape | Issue |
|---|---|---|
| `no_oversell`, `reserved_matches_reservations` | 2 servers on one database | [#17032](https://github.com/medusajs/medusa/issues/17032) |
| `no_oversell` | a cart with two lines on the same inventory item | [#16502](https://github.com/medusajs/medusa/issues/16502), and [#17032](https://github.com/medusajs/medusa/issues/17032) with more than one cart |
| `no_orphaned_orders` | more than one cart, completed together | [#16825](https://github.com/medusajs/medusa/issues/16825) |

Oversold has never reproduced #16825, so a `no_orphaned_orders` failure does not stop the sweep but is listed for a manual check, in the attempt's `manual_check` field and at the end of the sweep's output.

### Caps and the ledger

Every Oversold run and every paid call goes through a guard in `src/shortfall/budget.py`, which never starts a run set or a call that would go over a cap: 600 Oversold runs per session (`--max-runs` overrides it), 25 per attempt, and 0 dollars per session, which only `--raise-dollar-cap` can raise. Dollars also have a total cap of $20 across all sessions. At the start of every session the guard adds up the dollars already in the ledger, and it refuses any paid call that would take that total past $20. A paid call reserves its largest possible cost before it starts and settles to its real cost when it ends. When a cap is reached the run stops, writes what it has and prints what was used against each cap.

Each attempt writes to `runs/ledger.jsonl`, which is not committed, as it goes:

- a `started` line before it charges anything;
- a `spend` line for each Oversold run set, written before the set runs, and for each paid call a `reserved` line before the call and a `settled` line after it, with the model, input tokens, output tokens and dollars;
- a `final` line when it ends.

An attempt with a `started` line and no `final` line counts as interrupted, with every run and dollar it charged. A paid call with no `settled` line counts at its reservation. The `final` line holds the attempt id, the scenario path and its sha256, the case or none, the Medusa version and image, the cart and server counts, the runs used in the screen, the score and the control, each check's failures, the verdict, the cart setup error for an `unpreparable` candidate, the wall time, the Oversold runs and dollars used, any manual check, the Oversold commit and a UTC timestamp. Lines written before these kinds existed hold one complete attempt each and still count. `python -m shortfall.sweep --rerun <attempt id>` reruns one attempt from its ledger line on the same image and says whether the verdict came back the same.

## How to recheck

No Docker engine is needed. From the repo root:

```sh
make oversold
for d in benchmark/cases/*/results/*; do sh scripts/oversold.sh check --verify "$d"; done
```

`check --verify` recomputes every verdict and report from the saved histories and exits 0 only when they match the stored ones.
