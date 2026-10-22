# counter-two-servers

- Scenario file: `reference.yaml`, sha256 `faf4698ecae2f78c77f7ba4a0a6f4a9084ad8c203992bbc0d05c2970f4a6bde1`
- Medusa version in the file: 2.21.2. Version used: 2.19.0
- Oversold commit that ran it: `a18d5c9f3892dbca86effa0766e975985f8324bd` (clean)
- Verdicts computed by Oversold commit: `a18d5c9f3892dbca86effa0766e975985f8324bd` (clean)
- Server `medusa`: Medusa 2.19.0, image `sha256:170f4d29b9d544cdf96e06f7a75d4d3306f28abd80024cfdbe46044c0096e112`
- Server `medusa-2`: Medusa 2.19.0, image `sha256:170f4d29b9d544cdf96e06f7a75d4d3306f28abd80024cfdbe46044c0096e112`
- Postgres 15.19
- Runs: 30 of 30 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| reserved_matches_reservations | 1 | 30 of 30 | 0 of 30 | 0 of 30 |
| one_order_per_cart | 1 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_orphaned_orders | 1 | 0 of 30 | 30 of 30 | 0 of 30 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | History |
|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | fail | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | fail | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | fail | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | fail | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | fail | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | fail | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | fail | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | fail | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | fail | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | fail | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | fail | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | fail | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | fail | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | fail | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | fail | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | fail | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | fail | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | fail | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | fail | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | fail | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | fail | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | fail | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | fail | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | fail | pass | pass | [run-030.json.gz](run-030.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
- Run 11, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 12, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 13, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
- Run 14, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 15, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 16, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 17, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 18, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
- Run 19, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 20, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 21, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 22, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
- Run 23, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 24, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 25, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 26, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 27, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 28, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 29, reserved_matches_reservations fail: WIDGET reserved_quantity 6 but live reservations sum to 10
- Run 30, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 10
