# single-cart-over-demand

- Scenario file: `reference.yaml`, sha256 `d834f2853d9e881438d153ce326c9de1a8ead376b79d53d3b1f6362c638c7f3b`
- Medusa version in the file: 2.21.2. Version used: 2.22.0
- Oversold commit that ran it: `27169174ca97a2147ac39d70fae3fd29573131d4` (clean)
- Verdicts computed by Oversold commit: `27169174ca97a2147ac39d70fae3fd29573131d4` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:26e01f1395dc0cbd8c7f6503f6635280eba4196511b2a0b48148d342a51ac258`
- Postgres 15.19
- Runs: 30 of 30 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 1 | 30 of 30 | 0 of 30 | 0 of 30 |
| reserved_matches_reservations | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| one_order_per_cart | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_orphaned_orders | 1 | 0 of 30 | 30 of 30 | 0 of 30 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | History |
|---|---|---|---|---|---|
| 1 | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | fail | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | fail | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | fail | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | fail | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | fail | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | fail | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | fail | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | fail | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | fail | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | fail | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | fail | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | fail | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | fail | pass | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | fail | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | fail | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | fail | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | fail | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | fail | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | fail | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | fail | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 2, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 3, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 4, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 5, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 6, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 7, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 8, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 9, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 10, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 11, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 12, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 13, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 14, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 15, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 16, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 17, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 18, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 19, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 20, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 21, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 22, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 23, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 24, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 25, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 26, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 27, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 28, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 29, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
- Run 30, no_oversell fail: WIDGET live reservations 8 exceed stocked 6; WIDGET orders need 8 units but 6 were stocked at the start of the race
