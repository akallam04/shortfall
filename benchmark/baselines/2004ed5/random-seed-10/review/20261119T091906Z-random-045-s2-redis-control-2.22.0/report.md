# random-045-s2-redis-control

- Scenario file: `random-045-s2-redis-control.yaml`, sha256 `645d3bee456824a9ab50d00fd25ba98b107d4e10e49caa111d33cdcd175dee14`
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
- Scripted Redis lock calls during the race: 128 to 141 per run, recorded in 60 runs
- Runs: 60 of 60 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 20 of 60 | 40 of 60 | 0 of 60 |
| reserved_matches_reservations | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| one_order_per_cart | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_orphaned_orders | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_missing_orders | 1 | 0 of 60 | 60 of 60 | 0 of 60 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | Lock calls | History |
|---|---|---|---|---|---|---|---|
| 1 | fail | pass | pass | pass | pass | 133 | [run-001.json.gz](run-001.json.gz) |
| 2 | fail | pass | pass | pass | pass | 135 | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | 137 | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | 137 | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | 134 | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | 132 | [run-006.json.gz](run-006.json.gz) |
| 7 | fail | pass | pass | pass | pass | 135 | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | pass | pass | pass | pass | 135 | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | 135 | [run-009.json.gz](run-009.json.gz) |
| 10 | fail | pass | pass | pass | pass | 133 | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | pass | 135 | [run-011.json.gz](run-011.json.gz) |
| 12 | fail | pass | pass | pass | pass | 133 | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | 134 | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | 128 | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | pass | 132 | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | pass | 138 | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | pass | 134 | [run-017.json.gz](run-017.json.gz) |
| 18 | fail | pass | pass | pass | pass | 133 | [run-018.json.gz](run-018.json.gz) |
| 19 | fail | pass | pass | pass | pass | 134 | [run-019.json.gz](run-019.json.gz) |
| 20 | fail | pass | pass | pass | pass | 136 | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | pass | 135 | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | 141 | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | pass | 131 | [run-023.json.gz](run-023.json.gz) |
| 24 | fail | pass | pass | pass | pass | 134 | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | 133 | [run-025.json.gz](run-025.json.gz) |
| 26 | fail | pass | pass | pass | pass | 132 | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | pass | 130 | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | pass | 134 | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | 133 | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | pass | 139 | [run-030.json.gz](run-030.json.gz) |
| 31 | fail | pass | pass | pass | pass | 134 | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | 133 | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | 136 | [run-033.json.gz](run-033.json.gz) |
| 34 | fail | pass | pass | pass | pass | 137 | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | 132 | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | pass | pass | pass | pass | 140 | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | pass | pass | pass | pass | 137 | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | 135 | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | pass | pass | pass | pass | 136 | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | pass | pass | pass | pass | 135 | [run-040.json.gz](run-040.json.gz) |
| 41 | fail | pass | pass | pass | pass | 134 | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | pass | pass | pass | pass | 135 | [run-042.json.gz](run-042.json.gz) |
| 43 | fail | pass | pass | pass | pass | 135 | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | 139 | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | pass | pass | pass | pass | 136 | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | 136 | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | pass | pass | pass | pass | 132 | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | pass | pass | pass | pass | 134 | [run-048.json.gz](run-048.json.gz) |
| 49 | fail | pass | pass | pass | pass | 136 | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | pass | pass | pass | pass | 137 | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | pass | pass | pass | pass | 135 | [run-051.json.gz](run-051.json.gz) |
| 52 | fail | pass | pass | pass | pass | 129 | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | pass | pass | pass | pass | 134 | [run-053.json.gz](run-053.json.gz) |
| 54 | fail | pass | pass | pass | pass | 139 | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | 140 | [run-055.json.gz](run-055.json.gz) |
| 56 | fail | pass | pass | pass | pass | 137 | [run-056.json.gz](run-056.json.gz) |
| 57 | fail | pass | pass | pass | pass | 134 | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | pass | pass | pass | pass | 130 | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | pass | pass | pass | pass | 137 | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | pass | pass | pass | pass | 136 | [run-060.json.gz](run-060.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 2, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 7, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 8, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 10, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 12, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 18, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 19, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 20, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 24, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 26, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 31, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 34, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 41, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 43, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 49, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 52, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 54, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 56, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
- Run 57, no_oversell fail: WIDGET live reservations 9 exceed stocked 8; WIDGET orders need 9 units but 8 were stocked at the start of the race
