# attempt-03-agent-20261121t025734z-redis-control

- Scenario file: `b-redis.yaml`, sha256 `2bddbd16f48a581849997dd1bff213c2f4db5fe9a8a18d5f240cb519ce3b8fcb`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: redis
- Redis 7.4.11
- Scripted Redis lock calls during the race: 84 to 95 per run, recorded in 100 runs
- Runs: 100 of 100 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| reserved_matches_reservations | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| one_order_per_cart | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_orphaned_orders | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_missing_orders | 1 | 0 of 100 | 100 of 100 | 0 of 100 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | Lock calls | History |
|---|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | 87 | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | 89 | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | 87 | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | 90 | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | 91 | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | 86 | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | 87 | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | pass | 87 | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | 85 | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | 91 | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | pass | 87 | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | pass | 87 | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | 86 | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | 90 | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | pass | 91 | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | pass | 88 | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | pass | 90 | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | 89 | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | pass | 89 | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | pass | 92 | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | pass | 87 | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | 87 | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | pass | 94 | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | pass | 90 | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | 92 | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | pass | 90 | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | pass | 89 | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | pass | 94 | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | 91 | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | pass | 87 | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | pass | pass | pass | pass | 92 | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | 90 | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | 92 | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | pass | pass | pass | pass | 89 | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | 88 | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | pass | pass | pass | pass | 89 | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | pass | pass | pass | pass | 91 | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | 87 | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | pass | pass | pass | pass | 90 | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | pass | pass | pass | pass | 90 | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | pass | pass | pass | pass | 94 | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | pass | pass | pass | pass | 93 | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | pass | pass | pass | pass | 91 | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | 95 | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | pass | pass | pass | pass | 94 | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | 91 | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | pass | pass | pass | pass | 89 | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | pass | pass | pass | pass | 88 | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | pass | pass | pass | pass | 92 | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | pass | pass | pass | pass | 94 | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | pass | pass | pass | pass | 91 | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | pass | pass | pass | pass | 90 | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | pass | pass | pass | pass | 87 | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | pass | pass | pass | pass | 89 | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | 86 | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | 92 | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | pass | pass | pass | pass | 89 | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | pass | pass | pass | pass | 88 | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | pass | pass | pass | pass | 92 | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | pass | pass | pass | pass | 86 | [run-060.json.gz](run-060.json.gz) |
| 61 | pass | pass | pass | pass | pass | 90 | [run-061.json.gz](run-061.json.gz) |
| 62 | pass | pass | pass | pass | pass | 91 | [run-062.json.gz](run-062.json.gz) |
| 63 | pass | pass | pass | pass | pass | 91 | [run-063.json.gz](run-063.json.gz) |
| 64 | pass | pass | pass | pass | pass | 91 | [run-064.json.gz](run-064.json.gz) |
| 65 | pass | pass | pass | pass | pass | 88 | [run-065.json.gz](run-065.json.gz) |
| 66 | pass | pass | pass | pass | pass | 87 | [run-066.json.gz](run-066.json.gz) |
| 67 | pass | pass | pass | pass | pass | 92 | [run-067.json.gz](run-067.json.gz) |
| 68 | pass | pass | pass | pass | pass | 92 | [run-068.json.gz](run-068.json.gz) |
| 69 | pass | pass | pass | pass | pass | 90 | [run-069.json.gz](run-069.json.gz) |
| 70 | pass | pass | pass | pass | pass | 89 | [run-070.json.gz](run-070.json.gz) |
| 71 | pass | pass | pass | pass | pass | 87 | [run-071.json.gz](run-071.json.gz) |
| 72 | pass | pass | pass | pass | pass | 87 | [run-072.json.gz](run-072.json.gz) |
| 73 | pass | pass | pass | pass | pass | 90 | [run-073.json.gz](run-073.json.gz) |
| 74 | pass | pass | pass | pass | pass | 85 | [run-074.json.gz](run-074.json.gz) |
| 75 | pass | pass | pass | pass | pass | 91 | [run-075.json.gz](run-075.json.gz) |
| 76 | pass | pass | pass | pass | pass | 91 | [run-076.json.gz](run-076.json.gz) |
| 77 | pass | pass | pass | pass | pass | 91 | [run-077.json.gz](run-077.json.gz) |
| 78 | pass | pass | pass | pass | pass | 91 | [run-078.json.gz](run-078.json.gz) |
| 79 | pass | pass | pass | pass | pass | 89 | [run-079.json.gz](run-079.json.gz) |
| 80 | pass | pass | pass | pass | pass | 91 | [run-080.json.gz](run-080.json.gz) |
| 81 | pass | pass | pass | pass | pass | 89 | [run-081.json.gz](run-081.json.gz) |
| 82 | pass | pass | pass | pass | pass | 88 | [run-082.json.gz](run-082.json.gz) |
| 83 | pass | pass | pass | pass | pass | 90 | [run-083.json.gz](run-083.json.gz) |
| 84 | pass | pass | pass | pass | pass | 91 | [run-084.json.gz](run-084.json.gz) |
| 85 | pass | pass | pass | pass | pass | 88 | [run-085.json.gz](run-085.json.gz) |
| 86 | pass | pass | pass | pass | pass | 89 | [run-086.json.gz](run-086.json.gz) |
| 87 | pass | pass | pass | pass | pass | 88 | [run-087.json.gz](run-087.json.gz) |
| 88 | pass | pass | pass | pass | pass | 88 | [run-088.json.gz](run-088.json.gz) |
| 89 | pass | pass | pass | pass | pass | 87 | [run-089.json.gz](run-089.json.gz) |
| 90 | pass | pass | pass | pass | pass | 87 | [run-090.json.gz](run-090.json.gz) |
| 91 | pass | pass | pass | pass | pass | 84 | [run-091.json.gz](run-091.json.gz) |
| 92 | pass | pass | pass | pass | pass | 92 | [run-092.json.gz](run-092.json.gz) |
| 93 | pass | pass | pass | pass | pass | 91 | [run-093.json.gz](run-093.json.gz) |
| 94 | pass | pass | pass | pass | pass | 90 | [run-094.json.gz](run-094.json.gz) |
| 95 | pass | pass | pass | pass | pass | 88 | [run-095.json.gz](run-095.json.gz) |
| 96 | pass | pass | pass | pass | pass | 88 | [run-096.json.gz](run-096.json.gz) |
| 97 | pass | pass | pass | pass | pass | 89 | [run-097.json.gz](run-097.json.gz) |
| 98 | pass | pass | pass | pass | pass | 87 | [run-098.json.gz](run-098.json.gz) |
| 99 | pass | pass | pass | pass | pass | 92 | [run-099.json.gz](run-099.json.gz) |
| 100 | pass | pass | pass | pass | pass | 87 | [run-100.json.gz](run-100.json.gz) |
