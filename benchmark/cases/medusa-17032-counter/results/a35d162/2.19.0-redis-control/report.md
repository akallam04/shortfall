# counter-two-servers-redis-control

- Scenario file: `redis-control.yaml`, sha256 `a59097c096ca0862bf4ad61f6f56ba63ad2f92155fd659896f47a4b678c8ca94`
- Medusa version in the file: 2.21.2. Version used: 2.19.0
- Oversold commit that ran it: `a35d162cb5be383e7d3f9c6ffd91b306377144a8` (clean)
- Verdicts computed by Oversold commit: `a35d162cb5be383e7d3f9c6ffd91b306377144a8` (clean)
- Server `medusa`: Medusa 2.19.0, image `sha256:049de24eda1a6acd0accff0e90d036cd3ead1da1754ad01163ac819896f04876`
- Server `medusa-2`: Medusa 2.19.0, image `sha256:049de24eda1a6acd0accff0e90d036cd3ead1da1754ad01163ac819896f04876`
- Postgres 15.19
- Locking: redis
- Redis 7.4.11
- Scripted Redis lock calls during the race: 59 to 66 per run, recorded in 30 runs
- Runs: 30 of 30 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| reserved_matches_reservations | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| one_order_per_cart | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_orphaned_orders | 1 | 0 of 30 | 30 of 30 | 0 of 30 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | Lock calls | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | 63 | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | 63 | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | 60 | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | 61 | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | 60 | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | 65 | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | 63 | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | 64 | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | 60 | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | 64 | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | 64 | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | 65 | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | 62 | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | 63 | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | 59 | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | 64 | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | 62 | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | 64 | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | 62 | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | 63 | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | 64 | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | 66 | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | 60 | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | 65 | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | 65 | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | 62 | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | 63 | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | 64 | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | 60 | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | 63 | [run-030.json.gz](run-030.json.gz) |
