# last-unit-two-servers

- Scenario file: `reference.yaml`, sha256 `a24e3ffdbd46eb4068791751da9cfd460f5316af871417161d4154c7307a98c9`
- Medusa version in the file: 2.21.2. Version used: 2.21.2
- Oversold commit that ran it: `a18d5c9f3892dbca86effa0766e975985f8324bd` (clean)
- Verdicts computed by Oversold commit: `a18d5c9f3892dbca86effa0766e975985f8324bd` (clean)
- Server `medusa`: Medusa 2.21.2, image `sha256:8b684bf5b7c6af1b401200325dc4ff285f96bdf8c44e0a68f42b2408d77e0796`
- Server `medusa-2`: Medusa 2.21.2, image `sha256:8b684bf5b7c6af1b401200325dc4ff285f96bdf8c44e0a68f42b2408d77e0796`
- Postgres 15.19
- Runs: 30 of 30 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 1 | 20 of 30 | 10 of 30 | 0 of 30 |
| reserved_matches_reservations | 1 | 20 of 30 | 10 of 30 | 0 of 30 |
| one_order_per_cart | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_orphaned_orders | 1 | 0 of 30 | 30 of 30 | 0 of 30 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | History |
|---|---|---|---|---|---|
| 1 | fail | fail | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | fail | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | fail | fail | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | fail | fail | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | fail | fail | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | fail | fail | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | fail | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | fail | fail | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | fail | fail | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | fail | fail | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | fail | fail | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | fail | fail | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | fail | fail | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | fail | fail | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | fail | fail | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | fail | fail | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | fail | fail | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | fail | fail | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | fail | fail | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | fail | fail | pass | pass | [run-030.json.gz](run-030.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 1, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 3, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 3, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 4, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 4, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 5, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 5, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 6, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 6, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 7, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 7, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 8, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 8, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 9, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 9, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 10, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 10, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 12, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 12, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 13, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 13, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 14, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 14, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 15, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 15, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 16, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 16, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 18, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 18, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 21, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 21, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 22, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 22, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 23, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 23, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 28, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 28, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 30, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 30, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
