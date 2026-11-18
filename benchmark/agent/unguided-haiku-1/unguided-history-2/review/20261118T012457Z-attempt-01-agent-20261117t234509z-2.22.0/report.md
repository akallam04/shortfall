# attempt-01-agent-20261117t234509z

- Scenario file: `attempt-01.yaml`, sha256 `b19ccd426637e48ea27f53b2a166f13592b78625176d2d47ba859d258bc998c3`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 60 of 60 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 3 of 60 | 57 of 60 | 0 of 60 |
| reserved_matches_reservations | 2 | 60 of 60 | 0 of 60 | 0 of 60 |
| one_order_per_cart | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_orphaned_orders | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_missing_orders | 1 | 0 of 60 | 60 of 60 | 0 of 60 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | fail | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | fail | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | fail | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | fail | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | fail | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | fail | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | fail | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | fail | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | fail | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | fail | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | fail | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | fail | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | fail | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | fail | pass | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | fail | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | fail | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | fail | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | fail | fail | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | fail | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | fail | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | fail | fail | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | fail | pass | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | fail | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | fail | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | fail | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | fail | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | fail | pass | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | fail | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | fail | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | fail | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | fail | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | fail | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | fail | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | fail | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | fail | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | fail | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | fail | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | fail | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | fail | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | fail | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | fail | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | fail | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | fail | pass | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | fail | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | fail | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | fail | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | fail | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | fail | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | fail | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | fail | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | fail | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 11 exceed stocked 10; WIDGET orders need 11 units but 10 were stocked at the start of the race
- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 11
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 11, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 12, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 13, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 14, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 15, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 16, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 17, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 18, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 19, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 20, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 21, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 22, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 23, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 24, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 25, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 26, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 27, no_oversell fail: WIDGET live reservations 11 exceed stocked 10; WIDGET orders need 11 units but 10 were stocked at the start of the race
- Run 27, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 11
- Run 28, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 29, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 30, no_oversell fail: WIDGET live reservations 11 exceed stocked 10; WIDGET orders need 11 units but 10 were stocked at the start of the race
- Run 30, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 11
- Run 31, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 32, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 33, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 34, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 35, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 36, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 37, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 38, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 39, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 40, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 41, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 42, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 43, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 44, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 45, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 46, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 47, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 48, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 49, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 50, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 51, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 52, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 53, reserved_matches_reservations fail: WIDGET reserved_quantity 7 but live reservations sum to 10
- Run 54, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 55, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 56, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 57, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 58, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
- Run 59, reserved_matches_reservations fail: WIDGET reserved_quantity 9 but live reservations sum to 10
- Run 60, reserved_matches_reservations fail: WIDGET reserved_quantity 8 but live reservations sum to 10
