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

## How to recheck

No Docker engine is needed. From the repo root:

```sh
make oversold
for d in benchmark/cases/*/results/*; do sh scripts/oversold.sh check --verify "$d"; done
```

`check --verify` recomputes every verdict and report from the saved histories and exits 0 only when they match the stored ones.
