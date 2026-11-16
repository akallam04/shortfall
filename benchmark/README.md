# Benchmark

Each case is one public bug in an open-source commerce engine that [Oversold](https://github.com/akallam04/oversold) can reproduce on a local copy. The benchmark grades whether Shortfall can find it.

## A case

A case is a folder in [cases/](cases/) named after its id.

- `case.yaml`: what the case is.
- `reference.yaml`: an Oversold scenario written by hand that reproduces the bug.
- one file per control, named in `controls`, such as `pr-17420-control.yaml`.
- `answer.yaml`: the source files accepted as the cause, for the located result.
- `results/<pin>/<version>-<set>/`: the measured runs, grouped under the short Oversold commit they ran at and exported with `oversold export`: the scenario, `report.json`, `report.md` and every run's history, gzipped.

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
| `rule` | The Oversold check the bug breaks: `no_oversell`, `reserved_matches_reservations`, `one_order_per_cart`, `no_orphaned_orders` or `no_missing_orders`. |
| `controls[].file` | The control scenario's file in the folder. |
| `controls[].kind` | `variant`, `redis-locking` or `one-server`. |
| `controls[].role` | `scoring`, `cross-check` or `history`. Exactly one control is `scoring`. |
| `controls[].variant` | With `variant` only: an Oversold build variant at the pin. |
| `controls[].version` | With `variant` only: the variant's base version, one of the case's versions. |
| `reference.file` | The reference scenario's file in the folder. |
| `reference.source` | Where the reference scenario comes from. |
| `agent_sees.guided` | What the agent may read in the guided setting. |
| `agent_sees.unguided` | What the agent may read in the unguided setting. |
| `notes` | Optional notes. |

`load_case` in `src/shortfall/cases.py` reads a case strictly: an unknown field at any level is an error.

## Controls

A control is the same scenario on a build or setup where the bug should not happen, so a failure in the reference comes from the bug and not from the scenario. Every control file equals the rewrite of `reference.yaml` that `python -m shortfall.control` writes, byte for byte, and passes `oversold validate` at the pin.

- `variant`: the same scenario on one Oversold build variant that carries a fix, with `target.version` set to the variant's base version and `target.variant` added right after `target.servers`. `python -m shortfall.control --variant <name> <version> reference.yaml` writes it. The name gets `-<variant>-control` and the description says what it is. It refuses a scenario that already has a variant.
- `redis-locking`: the same scenario with `target.locking: redis`, so every Medusa server uses Medusa's Redis locking provider instead of the default in-memory one, which only locks inside one server process. `python -m shortfall.control --redis-locking reference.yaml` writes it.
- `one-server`: the same scenario with every server field set to 1. `python -m shortfall.control reference.yaml` writes it.

| Case | Scoring control | Cross-check | History |
|---|---|---|---|
| medusa-17032-last-unit | `pr-17420-control.yaml`: variant pr-17420 on 2.22.0 | `redis-control.yaml` on all three versions | `one-server-control.yaml` |
| medusa-17032-counter | `pr-17420-control.yaml`: variant pr-17420 on 2.22.0 | `redis-control.yaml` on all three versions | `one-server-control.yaml` |
| medusa-16502-lines | `pr-16961-control.yaml`: variant pr-16961 on 2.22.0 | none | none |

The variants come from Oversold's `variant.yaml` at the pin. pr-17420 is Medusa 2.22.0 with the change from [medusajs/medusa#17420](https://github.com/medusajs/medusa/pull/17420) by haranishi, which locks inventory level and reservation rows with `SELECT ... FOR UPDATE`. pr-16961 is Medusa 2.22.0 with the change from [medusajs/medusa#16961](https://github.com/medusajs/medusa/pull/16961) by pqa-labs, which checks the summed demand of entries that share an inventory item. Both pull requests were closed without being merged.

Each case has a scoring control only on 2.22.0, the base version of both variants.

## Results

The reference and control sets at Oversold v0.1.1, with the variant controls, are still to come. The sets below ran at earlier pins and were not run again.

Each row is one set of 30 runs at Oversold `a35d162`. "Rule failed" counts the runs where the case's rule failed. "Other checks failed" lists every other check that failed, with its number of failed runs.

| Case | Version | Set | Locking | Rule failed | Other checks failed | Inconclusive runs | Report |
|---|---|---|---|---|---|---|---|
| medusa-17032-last-unit | 2.21.2 | reference | in-memory | 25 of 30 | reserved_matches_reservations 25 | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.21.2-reference/report.md) |
| medusa-17032-last-unit | 2.21.2 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.21.2-redis-control/report.md) |
| medusa-17032-last-unit | 2.19.0 | reference | in-memory | 24 of 30 | reserved_matches_reservations 24 | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.19.0-reference/report.md) |
| medusa-17032-last-unit | 2.19.0 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.19.0-redis-control/report.md) |
| medusa-17032-last-unit | 2.22.0 | reference | in-memory | 24 of 30 | reserved_matches_reservations 24 | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.22.0-reference/report.md) |
| medusa-17032-last-unit | 2.22.0 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/a35d162/2.22.0-redis-control/report.md) |
| medusa-17032-counter | 2.21.2 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.21.2-reference/report.md) |
| medusa-17032-counter | 2.21.2 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.21.2-redis-control/report.md) |
| medusa-17032-counter | 2.19.0 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.19.0-reference/report.md) |
| medusa-17032-counter | 2.19.0 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.19.0-redis-control/report.md) |
| medusa-17032-counter | 2.22.0 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.22.0-reference/report.md) |
| medusa-17032-counter | 2.22.0 | redis-control | redis | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a35d162/2.22.0-redis-control/report.md) |
| medusa-16502-lines | 2.21.2 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/a35d162/2.21.2-reference/report.md) |
| medusa-16502-lines | 2.19.0 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/a35d162/2.19.0-reference/report.md) |
| medusa-16502-lines | 2.22.0 | reference | in-memory | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/a35d162/2.22.0-reference/report.md) |

In every Redis control run Medusa made scripted lock calls through Redis, read from Redis's `INFO commandstats` before and after the race: 8 to 10 per run for medusa-17032-last-unit and 59 to 66 per run for medusa-17032-counter. No run had a harness error.

A case is reproduced on a version when its rule failed in at least one reference run and in no control run. A case with no control is "reproduced, no control yet".

| Case | 2.21.2 | 2.19.0 | 2.22.0 |
|---|---|---|---|
| medusa-17032-last-unit | reproduced | reproduced | reproduced |
| medusa-17032-counter | reproduced | reproduced | reproduced |
| medusa-16502-lines | reproduced, no control yet | reproduced, no control yet | reproduced, no control yet |

The two #17032 cases fail with Medusa's default in-memory locking provider and not with its Redis locking provider. medusa-17032-last-unit's rule failed in 25, 24 and 24 of 30 reference runs on 2.21.2, 2.19.0 and 2.22.0, and in 0 of 30 Redis control runs on each. medusa-17032-counter's rule failed in 30 of 30 reference runs and in 0 of 30 Redis control runs on all three versions. Oversold's Medusa config uses the in-memory provider unless a scenario sets `target.locking: redis`. Medusa's docs recommend the Redis locking provider when more than one server runs.

### Earlier sets

These sets ran at earlier Oversold pins, on images built from those pins, with in-memory locking. The #17032 cases were controlled then by running the same scenario on one server.

| Case | Version | Oversold | Set | Rule failed | Other checks failed | Inconclusive runs | Report |
|---|---|---|---|---|---|---|---|
| medusa-17032-last-unit | 2.21.2 | `a18d5c9` | reference | 20 of 30 | reserved_matches_reservations 20 | 0 | [report](cases/medusa-17032-last-unit/results/a18d5c9/2.21.2-reference/report.md) |
| medusa-17032-last-unit | 2.21.2 | `a18d5c9` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/a18d5c9/2.21.2-control/report.md) |
| medusa-17032-last-unit | 2.19.0 | `a18d5c9` | reference | 25 of 30 | reserved_matches_reservations 25 | 0 | [report](cases/medusa-17032-last-unit/results/a18d5c9/2.19.0-reference/report.md) |
| medusa-17032-last-unit | 2.19.0 | `a18d5c9` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/a18d5c9/2.19.0-control/report.md) |
| medusa-17032-last-unit | 2.22.0 | `2716917` | reference | 24 of 30 | reserved_matches_reservations 24 | 0 | [report](cases/medusa-17032-last-unit/results/2716917/2.22.0-reference/report.md) |
| medusa-17032-last-unit | 2.22.0 | `2716917` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-last-unit/results/2716917/2.22.0-control/report.md) |
| medusa-17032-counter | 2.21.2 | `a18d5c9` | reference | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a18d5c9/2.21.2-reference/report.md) |
| medusa-17032-counter | 2.21.2 | `a18d5c9` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a18d5c9/2.21.2-control/report.md) |
| medusa-17032-counter | 2.19.0 | `a18d5c9` | reference | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a18d5c9/2.19.0-reference/report.md) |
| medusa-17032-counter | 2.19.0 | `a18d5c9` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/a18d5c9/2.19.0-control/report.md) |
| medusa-17032-counter | 2.22.0 | `2716917` | reference | 30 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2716917/2.22.0-reference/report.md) |
| medusa-17032-counter | 2.22.0 | `2716917` | one-server control | 0 of 30 | none | 0 | [report](cases/medusa-17032-counter/results/2716917/2.22.0-control/report.md) |
| medusa-16502-lines | 2.21.2 | `a18d5c9` | reference | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/a18d5c9/2.21.2-reference/report.md) |
| medusa-16502-lines | 2.19.0 | `a18d5c9` | reference | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/a18d5c9/2.19.0-reference/report.md) |
| medusa-16502-lines | 2.22.0 | `2716917` | reference | 30 of 30 | none | 0 | [report](cases/medusa-16502-lines/results/2716917/2.22.0-reference/report.md) |

## Setup

- Oversold at tag v0.1.1, commit `2004ed534b765a3b3341efaadb3f352ffdecef90`, from `oversold.lock`. No sets have run at this pin yet. The sets in the main results table ran at `a35d162cb5be383e7d3f9c6ffd91b306377144a8`. The earlier sets ran at `a18d5c9f3892dbca86effa0766e975985f8324bd` (2.21.2 and 2.19.0) and `27169174ca97a2147ac39d70fae3fd29573131d4` (2.22.0).
- At v0.1.1 Oversold has five checks: `no_oversell` 2, `reserved_matches_reservations` 2, `one_order_per_cart` 2, `no_orphaned_orders` 2 and `no_missing_orders` 1. Version 2 of the first four adds an inconclusive rule for an after snapshot that is missing rows or has an unreadable level quantity, and `no_orphaned_orders` 2 adds up reservations per order instead of per line. `no_missing_orders` 1 checks that every `ok` completion left exactly one saved order linked to its cart. Every saved history keeps the check names and versions it was judged with, and `check --verify` at v0.1.1 passes on all 30 earlier folders, which keep their version 1 verdicts. Shortfall reads each verdict's name and version from the history and records the versions in the ledger.
- Up to `a35d162` nothing under `internal/checks` or in `docs/checks.md` changed. Between `2716917` and `a35d162` Oversold added `target.locking`, a Redis service with no published port, and the `locking`, `redis_version` and `lock_calls` fields in histories and reports. It also changed `targets/medusa/app/medusa-config.ts`, which is built into the Medusa image, so every image was built again.
- Colima 0.10.3, profile `shortfall`: 4 CPUs, 6 GiB memory, 40 GiB disk, `vz` VM, `virtiofs` mount of this repo, read-only.
- Docker client 29.8.2.
- macOS 27.0.1 on Apple silicon.
- Images for the `a35d162` sets, built in Shortfall's engine from the `a35d162` clone after the earlier images were removed:
  - `oversold-medusa:2.21.2`: `sha256:c89e6efff2f8fd2df6ad9d375feabde2c6abd1427312b9f7a4a9aef521090a66`
  - `oversold-medusa:2.19.0`: `sha256:049de24eda1a6acd0accff0e90d036cd3ead1da1754ad01163ac819896f04876`
  - `oversold-medusa:2.22.0`: `sha256:0d05f169766253ac3a4a9ecb852e8cc4a72879e4b9173556af9e486023f84b2f`
  - `redis:7.4.11-alpine`: image `sha256:d9436322172a5b482c187bf1f363d3c4fea086fcca6b9c8a94de8f0f39ed3193`, digest `redis@sha256:d9436322172a5b482c187bf1f363d3c4fea086fcca6b9c8a94de8f0f39ed3193`. Every Redis history records Redis 7.4.11.
  - `postgres:15.19-alpine`: image `sha256:d2c2ced0372e855e4c257a9e9b5725f403847c01cfb64facbf2b21dbdadb2d74`, digest `postgres@sha256:d2c2ced0372e855e4c257a9e9b5725f403847c01cfb64facbf2b21dbdadb2d74`
- Images for the earlier sets:
  - `oversold-medusa:2.21.2` at `a18d5c9`: `sha256:8b684bf5b7c6af1b401200325dc4ff285f96bdf8c44e0a68f42b2408d77e0796`
  - `oversold-medusa:2.19.0` at `a18d5c9`: `sha256:170f4d29b9d544cdf96e06f7a75d4d3306f28abd80024cfdbe46044c0096e112`
  - `oversold-medusa:2.22.0` at `2716917`: `sha256:26e01f1395dc0cbd8c7f6503f6635280eba4196511b2a0b48148d342a51ac258`
- `a35d162` runs from 2026-11-01 21:49:59 UTC to 2026-11-01 22:41:53 UTC.
- Earlier 2.21.2 and 2.19.0 runs from 2026-10-22 06:28:45 UTC to 2026-10-22 06:59:12 UTC, and 2.22.0 runs from 2026-10-25 22:20:08 UTC to 2026-10-25 23:04:22 UTC.

Every history records the Medusa image ID of each server and the Oversold commit. All 900 match the images listed for the pin their set ran at, with no local changes.

Run sets from different sessions are comparable only when the Medusa image ID matches. Since `61c7d02` Oversold labels each image with a hash of the files it is built from and builds the image, its template database and the servers on the first run that needs them. `sh scripts/oversold.sh up` only starts Postgres, and `sh scripts/oversold.sh image <version> [variant]` prints an image's ID, digest and inputs label. At v0.1.1 Oversold's compose file and Dockerfile name the Node, Postgres and Redis base images by digest. The Postgres digest it names, `sha256:aae6554de426ae1990f1a939ff183a0299146cf7142a6f4c379c3357af9cc2d8`, differs from the one recorded above for the earlier sets.

Images are named `<prefix>:<version>`, and a variant image `<prefix>:<version>-<variant>`. The prefix is `OVERSOLD_IMAGE_PREFIX` in `.oversold/.env`, `oversold-medusa` by default, and `scripts/oversold.sh` reads it from there.

## What the agent reads

In the guided setting the agent reads the case's issue and the Medusa source for the case's version. In the unguided setting it reads only the source. Neither reads git history, changelogs, changesets or guides written for AI coding tools. The snapshots go in `snapshots/`, which is not committed. Their manifests are in [snapshots/](snapshots/).

### Source snapshots

`python -m shortfall.snapshot source <version>` makes a shallow, sparse clone of `https://github.com/medusajs/medusa.git` at tag `v<version>` with only the `packages/` folder, and checks that the clone is at the commit the tag points to. It removes `.git`, every `CHANGELOG.md`, `AGENTS.md` and `CLAUDE.md`, and every `.changeset` folder, and writes the result to `snapshots/medusa-<version>/packages/`.

`AGENTS.md` and `CLAUDE.md` are guides written for AI coding tools. Only 2.22.0 ships them: 82 of each, 345791 bytes in all, describing each package's internals, such as which cart workflows take a lock. Keeping them would give the 2.22.0 agent hints the other versions don't get, so every snapshot removes them.

`benchmark/snapshots/medusa-<version>.json` records the tag, its commit, each kind of file or folder removed with how many and why, the file count, the total bytes, size numbers for `.ts` files and one sha256. That sha256 is taken over one line per file, `<sha256 of the file>  <path relative to the snapshot>`, sorted by path. Building a snapshot a second time gave the same manifest for all three versions.

| Version | Tag commit | Files | Bytes | CHANGELOG.md removed | AGENTS.md and CLAUDE.md removed | .ts files | .ts median characters | .ts 90th percentile characters |
|---|---|---|---|---|---|---|---|---|
| 2.22.0 | `205aff40bacf` | 8984 | 32571862 | 82 | 82 and 82 | 5994 | 986 | 6677 |
| 2.21.2 | `020565398e43` | 8934 | 32125509 | 82 | 0 and 0 | 5971 | 983 | 6676 |
| 2.19.0 | `87d77fa1b56e` | 8760 | 29706300 | 81 | 0 and 0 | 5815 | 953 | 6373 |

No `.changeset` folder and no links were found under `packages/` in any of the three. The 90th percentile is the nearest-rank value.

### Issue snapshots

`python -m shortfall.snapshot issue <case-id>` fetches the title and opening post of the case's issue from the public GitHub API, without comments, and writes `snapshots/issues/<case-id>.md`: the title, the issue URL, the fetch time and the post. `benchmark/snapshots/issues.json` records the title, the issue's last update time, the fetch time, the snapshot's character count and its sha256. The issue text itself is not committed.

| Case | Issue | Characters |
|---|---|---|
| medusa-17032-last-unit | [#17032](https://github.com/medusajs/medusa/issues/17032) | 3908 |
| medusa-17032-counter | [#17032](https://github.com/medusajs/medusa/issues/17032) | 3908 |
| medusa-16502-lines | [#16502](https://github.com/medusajs/medusa/issues/16502) | 5382 |

### Tools

`src/shortfall/tools.py` gives the agent three read-only tools, each working inside one snapshot folder:

- `list_files(path)`: the files and folders directly under a folder, with each file's size.
- `read_file(path, start, end)`: numbered lines from `start` to `end`, at most 400 lines per call.
- `search(text, path)`: a plain-text, case-sensitive search under a file or folder, at most 50 matches, each with its file and line number and the line cut to 300 characters. Binary files are skipped.

Every result is plain text, cut at 40,000 characters with a note saying it was cut. Every path is relative to the snapshot folder. Absolute paths and `..` are refused, and so is any link that points outside the snapshot, so the tools cannot reach the cases, the results, the issue snapshots, the ledger, `.env`, `.oversold/` or anything else outside it.

## Baseline sweep

`python -m shortfall.sweep` is a baseline that uses no model. It writes candidate scenario files from a fixed parameter space and scores each one through the pinned Oversold on Medusa 2.22.0, the default `--version` and the only version where every case has a scoring control. The baseline and agent comparisons use 2.22.0 at this pin. It uses only fields the scenario format already has: the three seeded SKUs, cart count, lines per cart and their quantities, starting stock, server count and completion order. The generator in `src/shortfall/sweep.py` does not read the cases, their reference files or their controls. Only the scoring step in `src/shortfall/score.py` maps a result to a case. The grid was designed with knowledge of the bug shapes in the cases, so it is an informed baseline, not a blind one.

Candidates go in `runs/sweep/<UTC time>/`. Both modes give the same files in the same order for the same `--seed`.

- `--mode grid` walks 32 candidates in this order: 2 servers, then 1. Within each, carts holding OVS-SOLO 1, then OVS-PIECE 1, then OVS-PIECE 1 and OVS-TWOPACK 1. Within each, 2 carts, then 10, split evenly across the servers. Within each, stock `under` (only for the two-line carts), `short`, then `ample`, all completions released together. Then 4 candidates released one after another, with 2 carts and `short` stock: 2 servers with OVS-SOLO 1, 2 servers with OVS-PIECE 1 and OVS-TWOPACK 1, then the same two on 1 server.
- Stock levels, per inventory item: `under` is one cart's need minus 1, `short` is the total need minus one cart's need, and `ample` is 10 times the total need.
- `under` is used only for carts with more than one line. Medusa will not add a line to a cart when the stock is below that line's quantity, so a one-line cart with `under` stock can never be prepared. With two lines on the same item, each line still fits on its own while the cart as a whole does not, which is the shape behind #16502. The grid checks that every line fits the stock on its own.
- `--mode random --count N` samples N candidates from the same space with up to two cart groups, quantities from 1 to 3 and random stock and release.

### Scoring

The same code path in `src/shortfall/score.py` scores sweep candidates now and agent attempts later. A candidate that sets `target.variant` or `target.locking` is refused before it runs. Only the harness sets them.

Screen and retry:

1. Screen: run the candidate 3 times, once and then 2 more. If a run fails while preparing a cart, the candidate is `unpreparable` and the rest of its runs are skipped.
2. A candidate with a failed check in its screen goes to scoring at once.
3. After every candidate has had its first screen, leftover session runs pay for a second pass: 7 more runs for each candidate with no failure yet, in the original order. A failure there goes to scoring like any other.
4. A candidate with no failure is `not reproduced within N runs`, with N the runs it got. This never says a bug is absent.

Scoring runs the candidate 10 more times on plain Medusa 2.22.0. Then, for each rule that failed in those 10 runs, it runs the scoring control of every case with that rule, 10 times each. A control two cases share runs once. The server count never picks a case.

Each attempt gets three results:

- **violation**: `violation` when at least one check failed in the candidate's runs on plain Medusa, with each failed rule and its count. Otherwise `not reproduced within N runs`, `unpreparable`, or `inconclusive` when every run was inconclusive.
- **reproduced**, per case: `reproduced` when the case's rule failed in at least 1 of the 10 scoring runs and in 0 of the 10 runs on that case's scoring control, with no inconclusive control run. Otherwise `not reproduced`, or `inconclusive` when the control's rule held but a control run was inconclusive. A failed rule that no case's control clears is `violation, cause not isolated`, and it is not credited to any case.
- **located**: an attempt may name one source file as the cause. It is graded by exact path against `answer.yaml` for each case it reproduced. Grid and random candidates name no file, so their located result is `not applicable`.

| Case | Accepted files |
|---|---|
| medusa-16502-lines | `packages/modules/inventory/src/services/inventory-module.ts`, `packages/core/core-flows/src/cart/steps/confirm-inventory.ts` |
| medusa-17032-last-unit, medusa-17032-counter | `packages/modules/inventory/src/services/inventory-module.ts`, `packages/core/core-flows/src/cart/steps/reserve-inventory.ts`, `packages/modules/locking/src/providers/in-memory.ts`, the in-memory locking provider |

Every accepted path exists in the 2.22.0 source snapshot.

Inconclusive runs count against the caps like any other run, and so does the run that shows a candidate is `unpreparable`. The sweep stops when 3 attempts in a row have only inconclusive runs in their first screen, not counting `unpreparable` ones.

### Failures outside the public issues

Every failed check in every set is compared with this map of public issues. A failure the map does not cover stops the sweep at once, and nothing about it is pushed.

| Rule | Shape | Issue |
|---|---|---|
| `no_oversell`, `reserved_matches_reservations` | 2 servers on one database, with in-memory locking | [#17032](https://github.com/medusajs/medusa/issues/17032) |
| `no_oversell` | a cart with two lines on the same inventory item | [#16502](https://github.com/medusajs/medusa/issues/16502), and [#17032](https://github.com/medusajs/medusa/issues/17032) with more than one cart |
| `no_orphaned_orders` | more than one cart, completed together | [#16825](https://github.com/medusajs/medusa/issues/16825) |

A scenario with `target.locking: redis` is never covered by #17032. Two servers with in-memory locking stay covered by #17032, with or without a variant. On variant pr-16961, #16502 covers nothing. No public issue covers a `no_missing_orders` or a `one_order_per_cart` failure, so either stops the sweep.

Oversold has never reproduced #16825, so a `no_orphaned_orders` failure does not stop the sweep but is listed for a manual check, in the attempt's `manual_check` field and at the end of the sweep's output.

### Caps and the ledger

Every Oversold run and every paid call goes through a guard in `src/shortfall/budget.py`, which never starts a run set or a call that would go over a cap: 600 Oversold runs per session (`--max-runs` overrides it), 40 per attempt (3 screen runs, 7 retry runs, 10 scoring runs and up to two scoring controls of 10), and 0 dollars per session, which only `--raise-dollar-cap` can raise. Dollars also have a total cap of $20 across all sessions. At the start of every session the guard adds up the dollars already in the ledger, and it refuses any paid call that would take that total past $20. A paid call reserves its largest possible cost before it starts and settles to its real cost when it ends. When a cap is reached the run stops, writes what it has and prints what was used against each cap.

Each attempt writes to `runs/ledger.jsonl`, which is not committed, as it goes:

- a `started` line before it charges anything;
- a `spend` line for each Oversold run set, written before the set runs, and for each paid call a `reserved` line before the call and a `settled` line after it, with the model, input tokens, output tokens and dollars;
- a `final` line when it ends.

An attempt with a `started` line and no `final` line counts as interrupted, with every run and dollar it charged. A paid call with no `settled` line counts at its reservation. A candidate that waits for its second pass has a `started` line and its spend lines, and writes its `final` line when its second pass ends. The `final` line holds the attempt id, the scenario path and its sha256, the Medusa version and image, the cart and server counts, the runs in the screen, the retry, the scoring set and the controls, each check's failures per set, each scoring control with its cases, runs and failures, the check names and versions seen, the three results, the cart setup error for an `unpreparable` candidate, the wall time, the Oversold runs and dollars used, any manual check, the Oversold commit and a UTC timestamp. The sweep prints a summary of the three results for its own attempts. Lines written before the three results hold one complete attempt each and still count toward runs and dollars. `python -m shortfall.sweep --rerun <attempt id>` reruns one attempt from its ledger line on the same image and says whether the three results came back the same.

## How to recheck

No Docker engine is needed. From the repo root:

```sh
make oversold
for d in $(find benchmark/cases -name report.json -exec dirname {} \; | sort); do sh scripts/oversold.sh check --verify "$d"; done
```

`check --verify` recomputes every verdict and report from the saved histories and exits 0 only when they match the stored ones.
