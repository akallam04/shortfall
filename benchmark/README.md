# Benchmark

Each case is one public bug in an open-source commerce engine that [Oversold](https://github.com/akallam04/oversold) can reproduce on a local copy. The benchmark grades whether Shortfall can find it.

Today the benchmark is two known inventory failures in Medusa, measured through three scenarios. [#17032](https://github.com/medusajs/medusa/issues/17032) is a lost update across server processes, measured as the last unit sold twice (medusa-17032-last-unit) and as the reserved counter losing updates (medusa-17032-counter). [#16502](https://github.com/medusajs/medusa/issues/16502) is a stock check that looks at each cart line alone (medusa-16502-lines). #16502 needs no concurrency: its scenario completes one cart once.

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

Each row is one set of 30 runs on Medusa 2.22.0 at Oversold v0.1.1, commit `2004ed5`, with all five checks. Each check column counts the runs where that check failed, out of 30.

| Case | Set | no_oversell 2 | reserved_matches_reservations 2 | one_order_per_cart 2 | no_orphaned_orders 2 | no_missing_orders 1 | Inconclusive runs | Report |
|---|---|---|---|---|---|---|---|---|
| medusa-17032-last-unit | reference, plain Medusa | 23 | 23 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-last-unit/results/2004ed5/2.22.0-reference/report.md) |
| medusa-17032-last-unit | pr-17420, scoring control | 0 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-last-unit/results/2004ed5/2.22.0-pr-17420-control/report.md) |
| medusa-17032-last-unit | Redis locking, cross-check | 0 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-last-unit/results/2004ed5/2.22.0-redis-control/report.md) |
| medusa-17032-counter | reference, plain Medusa | 0 | 30 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-counter/results/2004ed5/2.22.0-reference/report.md) |
| medusa-17032-counter | pr-17420, scoring control | 0 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-counter/results/2004ed5/2.22.0-pr-17420-control/report.md) |
| medusa-17032-counter | Redis locking, cross-check | 0 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-17032-counter/results/2004ed5/2.22.0-redis-control/report.md) |
| medusa-16502-lines | reference, plain Medusa | 30 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-16502-lines/results/2004ed5/2.22.0-reference/report.md) |
| medusa-16502-lines | pr-16961, scoring control | 0 | 0 | 0 | 0 | 0 | 0 | [report](cases/medusa-16502-lines/results/2004ed5/2.22.0-pr-16961-control/report.md) |

No run in these sets was inconclusive, none had a complete call with outcome `unknown`, and none had a harness error. In the Redis control runs Medusa made 9 to 10 scripted lock calls through Redis per run for medusa-17032-last-unit and 57 to 68 for medusa-17032-counter.

Which fix clears which case, on 2.22.0:

- medusa-17032-last-unit: `no_oversell` failed in 23 of 30 runs on plain Medusa and in 0 of 30 with pr-17420. With Redis locking it failed in 0 of 30.
- medusa-17032-counter: `reserved_matches_reservations` failed in 30 of 30 runs on plain Medusa and in 0 of 30 with pr-17420. With Redis locking it failed in 0 of 30.
- medusa-16502-lines: `no_oversell` failed in 30 of 30 runs on plain Medusa and in 0 of 30 with pr-16961.

pr-16961 was not run on the #17032 scenarios, and pr-17420 was not run on the #16502 scenario.

| Case | 2.22.0 at v0.1.1 |
|---|---|
| medusa-17032-last-unit | reproduced: rule failed in 23 of 30 runs, 0 of 30 on its scoring control |
| medusa-17032-counter | reproduced: rule failed in 30 of 30 runs, 0 of 30 on its scoring control |
| medusa-16502-lines | reproduced: rule failed in 30 of 30 runs, 0 of 30 on its scoring control |

No case has a scoring control on 2.19.0 or 2.21.2, so the sets on those versions below are reproductions only.

### Sets at a35d162

Each row is one set of 30 runs at Oversold `a35d162`, judged by version 1 of the four checks that existed then. "Rule failed" counts the runs where the case's rule failed. "Other checks failed" lists every other check that failed, with its number of failed runs.

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

At this pin a case was counted as reproduced on a version when its rule failed in at least one reference run and in no control run. A case with no control was "reproduced, no control yet".

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

- Oversold at tag v0.1.1, commit `2004ed534b765a3b3341efaadb3f352ffdecef90`, from `oversold.lock`. The sets in the main results table ran at this commit. The sets at `a35d162cb5be383e7d3f9c6ffd91b306377144a8`, `a18d5c9f3892dbca86effa0766e975985f8324bd` (2.21.2 and 2.19.0) and `27169174ca97a2147ac39d70fae3fd29573131d4` (2.22.0) ran at earlier pins and were not run again.
- At v0.1.1 Oversold has five checks: `no_oversell` 2, `reserved_matches_reservations` 2, `one_order_per_cart` 2, `no_orphaned_orders` 2 and `no_missing_orders` 1. Version 2 of the first four adds an inconclusive rule for an after snapshot that is missing rows or has an unreadable level quantity, and `no_orphaned_orders` 2 adds up reservations per order instead of per line. `no_missing_orders` 1 checks that every `ok` completion left exactly one saved order linked to its cart. Every saved history keeps the check names and versions it was judged with, and `check --verify` at v0.1.1 passes on all 30 earlier folders, which keep their version 1 verdicts. Shortfall reads each verdict's name and version from the history and records the versions in the ledger.
- Up to `a35d162` nothing under `internal/checks` or in `docs/checks.md` changed. Between `2716917` and `a35d162` Oversold added `target.locking`, a Redis service with no published port, and the `locking`, `redis_version` and `lock_calls` fields in histories and reports. It also changed `targets/medusa/app/medusa-config.ts`, which is built into the Medusa image, so every image was built again.
- Colima 0.10.3, profile `shortfall`: 4 CPUs, 6 GiB memory, 40 GiB disk, `vz` VM, `virtiofs` mount of this repo, read-only.
- Docker client 29.8.2.
- macOS 27.0.1 on Apple silicon.
- Shortfall's engine was found empty on 2026-11-16, with no images, containers, volumes or build cache. Its Docker data disk had been created that day at the start of the session, so every image at this pin was built in one session, from the v0.1.1 clone. The VM still had one mount, this folder, read-only.
- Images for the `2004ed5` sets, built by Oversold's first run of each:
  - `oversold-medusa:2.22.0`: `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`, inputs label `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
  - `oversold-medusa:2.22.0-pr-17420`: `sha256:e3bcacbc669133e02b8372ceccf0e7184623625404fdf274a5880f392805e29a`, inputs label `47a24af91270797a42fcf8d465c9f25371b24cee68596902fef016ee7bc0af21`
  - `oversold-medusa:2.22.0-pr-16961`: `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`, inputs label `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
  - Every history records the image ID and inputs label of each server, and every variant history the sha256 of each replaced file. All 240 match the images above and the variant files in Oversold's `variant.yaml`.
- Base images for the `2004ed5` sets, read from the engine, not from the histories, which record only the Postgres and Redis versions. They were read once before the first set and once after the last, and both readings equal the digests pinned in the clone's `compose.yaml` and `Dockerfile`:
  - `postgres:15.19-alpine`: `postgres@sha256:aae6554de426ae1990f1a939ff183a0299146cf7142a6f4c379c3357af9cc2d8`, the image of the running Postgres container. Every history records Postgres 15.19.
  - `redis:7.4.11-alpine`: `redis@sha256:d9436322172a5b482c187bf1f363d3c4fea086fcca6b9c8a94de8f0f39ed3193`, the image of the running Redis container at the end. It was not yet in the engine before the first set. Every Redis history records Redis 7.4.11.
  - `node:22.23.3-bookworm-slim`: not kept in the image store. The build cache records it as pulled from `docker.io/library/node:22.23.3-bookworm-slim@sha256:3ed98443660ff48413b5af19ecefce3b9d50845a901a43420d47cc63a9fddbe9`.
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
- `2004ed5` runs from 2026-11-16 19:42:44 UTC to 2026-11-16 20:09:50 UTC.
- `a35d162` runs from 2026-11-01 21:49:59 UTC to 2026-11-01 22:41:53 UTC.
- Earlier 2.21.2 and 2.19.0 runs from 2026-10-22 06:28:45 UTC to 2026-10-22 06:59:12 UTC, and 2.22.0 runs from 2026-10-25 22:20:08 UTC to 2026-10-25 23:04:22 UTC.

Every history records the Medusa image ID of each server and the Oversold commit. All 1140 match the images listed for the pin their set ran at, with no local changes.

Run sets from different sessions are comparable only when the Medusa image ID matches. Since `61c7d02` Oversold labels each image with a hash of the files it is built from and builds the image, its template database and the servers on the first run that needs them. `sh scripts/oversold.sh up` only starts Postgres, and `sh scripts/oversold.sh image <version> [variant]` prints an image's ID, digest and inputs label. At v0.1.1 Oversold's compose file and Dockerfile name the Node, Postgres and Redis base images by digest. The Postgres digest differs from the one recorded below for the `a35d162` sets.

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

Each sweep session is one trial, with a hard cap of 300 Oversold runs (`--max-runs`) that covers screens, retries, scoring runs and control runs. Candidates go in `runs/sweep/<UTC time>/`. Both modes give the same files in the same order for the same seeds. Before any run, the trial writes a `trial` line to the ledger with the candidate names and one sha256 over each candidate's name and scenario text, in trial order, so the list is fixed before anything runs.

- `--mode grid` walks 32 candidates in this order: 2 servers, then 1. Within each, carts holding OVS-SOLO 1, then OVS-PIECE 1, then OVS-PIECE 1 and OVS-TWOPACK 1. Within each, 2 carts, then 10, split evenly across the servers. Within each, stock `under` (only for the two-line carts), `short`, then `ample`, all completions released together. Then 4 candidates released one after another, with 2 carts and `short` stock: 2 servers with OVS-SOLO 1, 2 servers with OVS-PIECE 1 and OVS-TWOPACK 1, then the same two on 1 server. `--order-seed N` shuffles this order with seed N. The 32 shapes and their scenario text do not change.
- Stock levels, per inventory item: `under` is one cart's need minus 1, `short` is the total need minus one cart's need, and `ample` is 10 times the total need.
- `under` is used only for carts with more than one line. Medusa will not add a line to a cart when the stock is below that line's quantity, so a one-line cart with `under` stock can never be prepared. With two lines on the same item, each line still fits on its own while the cart as a whole does not, which is the shape behind #16502. The grid checks that every line fits the stock on its own.
- `--mode random` draws candidates from `--seed`, one after another, from the same space with up to two cart groups, quantities from 1 to 3 and random stock and release. By default it draws as many as the run cap can screen, 300 / 3 = 100, so the budget runs out before the list does. `--count N` draws N instead.

### Scoring

The same code path in `src/shortfall/score.py` scores sweep candidates now and agent attempts later. A candidate that sets `target.variant`, `target.locking` or `checks` is refused before it runs. Only the harness sets the target fields, and every run uses every check. A run with any complete call whose outcome is `unknown` counts as inconclusive, for the candidate and for controls, since Oversold's `no_missing_orders` skips a cart with an unknown call.

Screen and retry:

1. Screen: run the candidate 3 times, once and then 2 more. If a run fails while preparing a cart, the candidate is `unpreparable` and the rest of its runs are skipped.
2. A candidate with a failed check in its screen goes to scoring at once.
3. After every candidate has had its first screen, leftover session runs pay for a second pass: 7 more runs for each candidate with no failure yet, in the original order. A failure there goes to scoring like any other.
4. A candidate with no failure is `not reproduced within N runs`, with N the runs it got. This never says a bug is absent.

Scoring runs the candidate 10 more times on plain Medusa 2.22.0. Then, for each rule that failed in those 10 runs, it runs the scoring control of every case with that rule, 10 times each. A control two cases share runs once. The server count never picks a case.

Each attempt gets three results:

- **violation**: `violation` when at least one check failed in the candidate's runs on plain Medusa, with each failed rule and its count. Otherwise `not reproduced within N runs`, `unpreparable`, or `inconclusive` when every run was inconclusive.
- **reproduced**, per case: `reproduced` when the case's rule failed in at least 1 of the 10 scoring runs and in 0 of the 10 runs on that case's scoring control, with no inconclusive control run. Otherwise `not reproduced`, or `inconclusive` when the control's rule held but a control run was inconclusive. A failed rule that no case's control clears is `violation, cause not isolated`, and it is not credited to any case. It always goes into the attempt's `manual_check` field and the list at the end of the sweep. A failed rule whose scoring controls did not all run because the attempt reached a run cap is `cut off by the run cap` instead.
- **located**: an attempt may name one source file and one cause from the cause list. For each case it reproduced, the file is graded by exact path against the case's `answer.yaml`, the cause by id, and located needs both. The three results are kept apart. Grid and random candidates name neither, so their located result is `not applicable`.

The causes are fixed in [causes.yaml](causes.yaml):

| Cause | Meaning | Cases |
|---|---|---|
| `per-line-check` | Each line or entry is checked against stock alone, and entries that share an item are never added up. | medusa-16502-lines |
| `process-local-lock` | The lock only works inside one server process. | medusa-17032-last-unit, medusa-17032-counter |
| `stale-counter-write` | A counter is written from a value read earlier, so one update is lost. | medusa-17032-last-unit, medusa-17032-counter |
| `duplicate-completion` | The same cart is completed twice and both go through. | none |
| `payment-order-link` | An order is saved without its payment or cart link. | none |
| `stock-location-mixup` | Stock is read at one location and reserved at another. | none |

| Case | Accepted files |
|---|---|
| medusa-16502-lines | `packages/modules/inventory/src/services/inventory-module.ts`, `packages/core/core-flows/src/cart/steps/confirm-inventory.ts` |
| medusa-17032-last-unit, medusa-17032-counter | `packages/modules/inventory/src/services/inventory-module.ts`, `packages/core/core-flows/src/cart/steps/reserve-inventory.ts`, `packages/modules/locking/src/providers/in-memory.ts`, the in-memory locking provider |

Every accepted path exists in the 2.22.0 source snapshot. All three cases accept `inventory-module.ts`, so a file alone says little. `fixed_guess` in `src/shortfall/answers.py` scores one fixed guess over all three cases, and any located number Shortfall reports belongs next to these:

| Fixed guess | File accepted | Cause accepted | Located |
|---|---|---|---|
| always `inventory-module.ts`, no cause | 3 of 3 | 0 of 3 | 0 of 3 |
| always the most common cause, `process-local-lock`, no file | 0 of 3 | 2 of 3 | 0 of 3 |
| always `inventory-module.ts` and `process-local-lock` | 3 of 3 | 2 of 3 | 2 of 3 |

`process-local-lock` and `stale-counter-write` tie as the most common cause, and either gives the same scores.

Inconclusive runs count against the caps like any other run, and so does the run that shows a candidate is `unpreparable`. The sweep stops when 3 attempts in a row have only inconclusive runs in their first screen, not counting `unpreparable` ones.

### Failures outside the public issues

Every failed check in every set is compared with this map of public issues. A failure the map does not cover stops the sweep at once, and nothing about it is pushed.

| Rule | Shape | Issue |
|---|---|---|
| `no_oversell`, `reserved_matches_reservations` | 2 servers on one database, with in-memory locking | [#17032](https://github.com/medusajs/medusa/issues/17032) |
| `no_oversell` | a cart with two lines on the same inventory item | [#16502](https://github.com/medusajs/medusa/issues/16502), and [#17032](https://github.com/medusajs/medusa/issues/17032) with more than one cart |
| `no_orphaned_orders` | more than one cart, completed together | [#16825](https://github.com/medusajs/medusa/issues/16825) |

A scenario with `target.locking: redis` is never covered by #17032. Two servers with in-memory locking stay covered by #17032, with or without a variant. On variant pr-16961, #16502 covers nothing. No public issue covers a `no_missing_orders` or a `one_order_per_cart` failure, so either stops the sweep.

Oversold has never reproduced #16825, so a `no_orphaned_orders` failure does not stop the sweep but is listed for a manual check, in the attempt's `manual_check` field and at the end of the sweep's output. Any `violation, cause not isolated` is listed the same way, whatever this map says. The map stays the hard stop.

### Caps and the ledger

Every Oversold run and every paid call goes through a guard in `src/shortfall/budget.py`, which never starts a run set or a call that would go over a cap: 600 Oversold runs per session for any other use, and 300 per sweep trial (`--max-runs` overrides it), 40 per attempt (3 screen runs, 7 retry runs, 10 scoring runs and up to two scoring controls of 10), and 0 dollars per session, which only `--raise-dollar-cap` can raise. Dollars also have a total cap of $20 across all sessions. At the start of every session the guard adds up the dollars already in the ledger, and it refuses any paid call that would take that total past $20. A paid call reserves its largest possible cost before it starts and settles to its real cost when it ends. When a cap is reached the run stops, writes what it has and prints what was used against each cap.

Each attempt writes to `runs/ledger.jsonl`, which is not committed, as it goes:

- a `started` line before it charges anything;
- a `spend` line for each Oversold run set, written before the set runs, and for each paid call a `reserved` line before the call and a `settled` line after it, with the model, input tokens, output tokens and dollars;
- a `final` line when it ends.

An attempt with a `started` line and no `final` line counts as interrupted, with every run and dollar it charged. A paid call with no `settled` line counts at its reservation. A candidate that waits for its second pass has a `started` line and its spend lines, and writes its `final` line when its second pass ends. The `final` line holds the attempt id, the scenario path and its sha256, the Medusa version and image, the cart and server counts, the runs in the screen, the retry, the scoring set and the controls, each check's failures per set, each scoring control with its cases, runs and failures, the check names and versions seen, the three results, the cart setup error for an `unpreparable` candidate, the wall time, the Oversold runs and dollars used, any manual check, the Oversold commit and a UTC timestamp. The sweep prints a summary of the three results for its own attempts. Lines written before the three results hold one complete attempt each and still count toward runs and dollars. `python -m shortfall.sweep --rerun <attempt id>` reruns one attempt from its ledger line on the same image and says whether the three results came back the same.

## Baselines

Two baselines that use no model, measured on Medusa 2.22.0 at Oversold v0.1.1, commit `2004ed5`, on the images listed under Setup. Each trial is one sweep session with a hard cap of 300 Oversold runs, which covers screens, retries, scoring runs and control runs, and each is scored as described above.

- **Grid** varies the server count (1 or 2), the lines in each cart (OVS-SOLO 1, OVS-PIECE 1, or OVS-PIECE 1 with OVS-TWOPACK 1), the cart count (2 or 10), the stock level (`under`, `short` or `ample`) and the release (together, or one after another for 4 shapes). It was designed with knowledge of the bug shapes in the cases, so it is an informed baseline. An order seed shuffles its 32 shapes.
- **Random** varies the server count, up to two cart groups of 1 to 10 carts, one or two of the three SKUs per cart with quantities from 1 to 3, the stock of each item from 0 to twice its demand, and the release. It was not designed from the cases. Each trial draws 100 candidates from its seed.

Each row is one trial. "Runs to first" is the number of runs the trial had used when the case was first reproduced, counting from the trial's first run. Trials 1 to 3 of each method ran first. Trials 4 to 10 ran in the agent plan [scale-10](agent/README.md#plan-scale-10), between its agent trials, on the same images and Oversold commit.

| Trial | Candidates reached | Runs used | Cases reproduced | Runs to first: medusa-17032-last-unit | medusa-17032-counter | medusa-16502-lines | Violations | Cause not isolated | Cut off by the run cap |
|---|---|---|---|---|---|---|---|---|---|
| [grid order seed 1](baselines/2004ed5/grid-seed-1/) | 16 of 32 | 298 | 3 of 3 | 144 | 39 | 29 | 10 | 0 | 0 |
| [grid order seed 2](baselines/2004ed5/grid-seed-2/) | 21 of 32 | 293 | 3 of 3 | 81 | 81 | 26 | 10 | 0 | 1 |
| [grid order seed 3](baselines/2004ed5/grid-seed-3/) | 19 of 32 | 297 | 3 of 3 | 33 | 33 | 157 | 11 | 0 | 1 |
| [grid order seed 4](baselines/2004ed5/grid-seed-4/) | 19 of 32 | 297 | 3 of 3 | 121 | 33 | 23 | 10 | 0 | 1 |
| [grid order seed 5](baselines/2004ed5/grid-seed-5/) | 20 of 32 | 300 | 3 of 3 | 33 | 33 | 196 | 10 | 0 | 1 |
| [grid order seed 6](baselines/2004ed5/grid-seed-6/) | 20 of 32 | 300 | 3 of 3 | 33 | 33 | 124 | 9 | 0 | 0 |
| [grid order seed 7](baselines/2004ed5/grid-seed-7/) | 19 of 32 | 297 | 3 of 3 | 36 | 36 | 134 | 10 | 0 | 1 |
| [grid order seed 8](baselines/2004ed5/grid-seed-8/) | 25 of 32 | 295 | 3 of 3 | 209 | 23 | 52 | 10 | 0 | 1 |
| [grid order seed 9](baselines/2004ed5/grid-seed-9/) | 20 of 32 | 300 | 3 of 3 | 107 | 74 | 35 | 10 | 0 | 1 |
| [grid order seed 10](baselines/2004ed5/grid-seed-10/) | 20 of 32 | 300 | 3 of 3 | 33 | 33 | 56 | 9 | 0 | 0 |
| [random seed 1](baselines/2004ed5/random-seed-1/) | 51 of 100 | 299 | 2 of 3 | 170 | 42 | not reproduced | 7 | 0 | 1 |
| [random seed 2](baselines/2004ed5/random-seed-2/) | 48 of 100 | 296 | 3 of 3 | 103 | 103 | 51 | 7 | 0 | 1 |
| [random seed 3](baselines/2004ed5/random-seed-3/) | 59 of 100 | 291 | 2 of 3 | 117 | 36 | not reproduced | 6 | 0 | 1 |
| [random seed 4](baselines/2004ed5/random-seed-4/) | 40 of 100 | 300 | 3 of 3 | 213 | 59 | 26 | 7 | 1 | 0 |
| [random seed 5](baselines/2004ed5/random-seed-5/) | 70 of 100 | 300 | 3 of 3 | 142 | 87 | 29 | 5 | 0 | 1 |
| [random seed 6](baselines/2004ed5/random-seed-6/) | 62 of 100 | 300 | 3 of 3 | 46 | 46 | 176 | 5 | 0 | 0 |
| [random seed 7](baselines/2004ed5/random-seed-7/) | 44 of 100 | 300 | 3 of 3 | 97 | 47 | 126 | 7 | 0 | 0 |
| [random seed 8](baselines/2004ed5/random-seed-8/) | 67 of 100 | 291 | 2 of 3 | not reproduced | 33 | 86 | 6 | 0 | 1 |
| [random seed 9](baselines/2004ed5/random-seed-9/) | 54 of 100 | 298 | 2 of 3 | 47 | 47 | not reproduced | 7 | 0 | 0 |
| [random seed 10](baselines/2004ed5/random-seed-10/) | 52 of 100 | 300 | 3 of 3 | 62 | 26 | 145 | 6 | 1 | 0 |

The median below is taken over all 10 trials, and a trial that missed a case counts as over 300 runs.

- Grid, across its 10 trials: each case was reproduced in 10 of 10 trials, with a median of 58.5 runs to first reproduction for medusa-17032-last-unit, 33 for medusa-17032-counter and 54 for medusa-16502-lines. Every grid trial reproduced all three cases.
- Random, across its 10 trials: medusa-17032-counter was reproduced in 10 of 10 trials, with a median of 46.5 runs, medusa-17032-last-unit in 9 of 10, with a median of 110, and medusa-16502-lines in 7 of 10, with a median of 135.5. Six trials reproduced all three cases.

Located is `not applicable` for both baselines, since they name no file and no cause. Ten trials per method is still a small sample, and no difference in this table is called significant.

What else the trials show:

- No trial reached a second pass. Each one spent its 300 runs before every candidate had its first screen, so no candidate got more than its first 3 runs unless it failed.
- In 12 trials the last attempt found a violation but reached the 300-run cap before its scoring controls could run, so it is `cut off by the run cap`. The five of these in trials 1 to 3 were written to the ledgers before the label existed, as `violation, cause not isolated` with a manual check note, and the summary reads them as cut off because their stop reason is the run cap and their controls did not all run.
- pr-16961 left `no_oversell` failing only on two-server candidates, and pr-17420 left it failing only on candidates with two lines on one item, so each oversell was credited only to the case whose control cleared it.
- Random seeds 4 and 10 each had one `violation, cause not isolated`: a candidate with several carts on two servers, some with two lines on one item, where `no_oversell` kept failing with each fix on its own. Each was held and run again after the trial, 60 times on each of four sets. These runs were made only to decide whether to publish the trial, and they do not change its score. Both trials are labeled "covered by #16502 and #17032 together", and the runs are in each trial's `review/` folder. Seed 10's folder also holds the first review, which tried pr-17420 and Redis locking one at a time.

| Trial | Check | Plain Medusa | pr-16961 with Redis locking | pr-16961 alone | Redis locking alone |
|---|---|---|---|---|---|
| random seed 4 | `no_oversell` | 60 of 60 | 0 of 60 | 56 of 60 | 13 of 60 |
| random seed 10 | `no_oversell` | 58 of 60 | 0 of 60 | 49 of 60 | 20 of 60 |

- The grid trials had no inconclusive run. In the random trials, 5 to 15 candidates per trial could not be prepared, and 0 to 21 runs per trial had a complete call that ended in HTTP 500, which counts as inconclusive.
- No trial stopped for a failure outside the coverage map, a `no_missing_orders` failure or a harness error.

The candidate list of each trial was fixed before it ran. These are the sha256 values in each trial's `trial` ledger line:

- grid-seed-1: `9e716126af7a412a5f3143d6f7271fe178ece01fa306f23cb29a5ab07d623e36`
- grid-seed-2: `28a3304ef5f532d65fd39b7432d697ae7efd703f951439d7d04862d75664227c`
- grid-seed-3: `7ad631c3840dee08cee096f4aef48705617abcbb24008cf92270fca73642efa7`
- grid-seed-4: `7e779763e08aa381b83549816c06b06d37a036aa68d24412e30e2a4ae72f2210`
- grid-seed-5: `df39d0b583549dda225e365747353d5dd791f1952dcfbe1108743e6c73a3ab48`
- grid-seed-6: `47f30b837ffac6519a9a695b9985b7bfa816412c24c34c85d8d9561aa2f3e936`
- grid-seed-7: `8de2af6688df1119bfe73420241603a8e77b02740fd4c026873a6494fe93a792`
- grid-seed-8: `f23559cfd3cf0e51f9272f7de8c8a41e17345379b7c32278d204457b87f49430`
- grid-seed-9: `f058febbb2fc7686d4e7dce5c4b7ca543a60ea1393fb29795240832439830877`
- grid-seed-10: `afb993a7cbccf6e7babf1906fca11f759bbf887df0a083ab01ef42917084bb91`
- random-seed-1: `c715bc8bb32aee5b81019227beb11056abe6443d6d64ac2f4b78366427830f7f`
- random-seed-2: `0a5eb2c2f8d3530d4f068867b6bed3d316acc40ba5e1c5f690756857f6c3a8f8`
- random-seed-3: `be2fc026d6151b318507f4af127bf30c06561a90ef3717651cf2110895e40e63`
- random-seed-4: `613fd66b874bfa0b81bcca7e1acfefa4fdd5a7dd8312c56e9d5c00f5e34291a0`
- random-seed-5: `b7a0216392258cc63a913657d0bfe4556ce336a6c1a6c6640b004006239b0349`
- random-seed-6: `8e3bd4b3b26b21e81ecea4eb385510383f053ce3a6b975608f12ac2bb9898cb0`
- random-seed-7: `960af6997f8afbe41afdd047b7e5813b120ebab144f8b7488ae1dc21386a6c11`
- random-seed-8: `18cf0dead15dd3f1291342b88481eb3011b314a682c85f3c8939b9e0d26df71f`
- random-seed-9: `23a560e04d6f162d8b8ddf7de274f1984ffcf071c2a1d81045a5529f77dfc2d8`
- random-seed-10: `4b1d999b0891cbb6e2bc0c27a5283b7132c3f9b0af13ad88282a72f5931f113d`

Each trial's folder holds its `ledger.jsonl`, its candidate files in trial order under `candidates/`, every run set it ran under `runs/`, exported with `oversold export`, and for seeds 4 and 10 the review runs under `review/`.

## How to recheck

No Docker engine is needed. From the repo root:

```sh
make oversold
for d in $(find benchmark -name report.json -exec dirname {} \; | sort); do sh scripts/oversold.sh check --verify "$d"; done
```

`check --verify` recomputes every verdict and report from the saved histories and exits 0 only when they match the stored ones.
