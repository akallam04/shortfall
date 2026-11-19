# random-011-s2-pr-16961-control

- Scenario file: `random-011-s2-pr-16961-control.yaml`, sha256 `7c5fe1df188a4ab96e0673ac6f1f5b5a5452787bdb40a653157af94c56e44c14`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Variant `pr-16961`: Medusa 2.22.0 with the source change of https://github.com/medusajs/medusa/pull/16961 by pqa-labs (closed, not merged), head commit `5ac8ae437ee0b7771a945b5b30f265b76f214172`
  - Replaces `@medusajs/inventory/dist/services/inventory-module.js`, sha256 `8e150f6b9de7bc64f431e91a803716646a782379d3cc993a31f301056d5ac919` (was `6d2643ef94e7ffe20fb2b4a35f8f1de503ad4429c85c64cc4262ceae2a776c58`)
  - Replaces `@medusajs/core-flows/dist/cart/steps/confirm-inventory.js`, sha256 `2af8432c719836364a143d9fe7f4ee6f9aba17062d555e2fdace47315c11c569` (was `01a7cf229b6854a7840207c6ba62234bbdedc651adfd50276536e06d6e46134d`)
- Server `medusa`: Medusa 2.22.0, image `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`
  - Image inputs sha256 `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`
  - Image inputs sha256 `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
- Postgres 15.19
- Locking: in-memory
- Runs: 60 of 60 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 56 of 60 | 4 of 60 | 0 of 60 |
| reserved_matches_reservations | 2 | 59 of 60 | 1 of 60 | 0 of 60 |
| one_order_per_cart | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_orphaned_orders | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_missing_orders | 1 | 0 of 60 | 60 of 60 | 0 of 60 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | fail | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | fail | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | fail | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | fail | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | fail | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | fail | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | fail | fail | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | fail | fail | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | fail | fail | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | fail | fail | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | fail | fail | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | fail | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | fail | fail | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | fail | fail | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | fail | fail | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | fail | fail | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | fail | fail | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | fail | fail | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | fail | fail | pass | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | fail | fail | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | fail | fail | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | fail | fail | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | fail | fail | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | fail | fail | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | fail | fail | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | fail | fail | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
| 31 | fail | fail | pass | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | fail | fail | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | fail | fail | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | fail | fail | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | fail | fail | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | fail | fail | pass | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | fail | fail | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | fail | fail | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | fail | fail | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | fail | fail | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | fail | fail | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | fail | fail | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | fail | fail | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | fail | fail | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | fail | fail | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | fail | fail | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | fail | fail | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | fail | fail | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | fail | fail | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | fail | fail | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | fail | fail | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | fail | pass | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | fail | fail | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | fail | fail | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | fail | fail | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | fail | fail | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | fail | fail | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | fail | fail | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | fail | fail | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | fail | fail | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 2, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 3, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 4, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 5, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 24 but live reservations sum to 36
- Run 6, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 26
- Run 8, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 10, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 11, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 11, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 12, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 12, reserved_matches_reservations fail: WIDGET reserved_quantity 24 but live reservations sum to 36
- Run 13, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 13, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 14, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 14, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 15, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 15, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 16, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 26
- Run 17, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 17, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 18, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 18, reserved_matches_reservations fail: WIDGET reserved_quantity 24 but live reservations sum to 36
- Run 19, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 19, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 20, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 20, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 21, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 21, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 22, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 22, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 23, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 23, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 24, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 24, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 25, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 25, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 26, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 26, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 27, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 27, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 28, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 28, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 29, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 29, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 30, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 30, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 31, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 31, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 32, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 32, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 33, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 33, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 34, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 34, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 35, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 35, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 36, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 36, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 37, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 37, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 38, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 38, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 39, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 39, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 40, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 40, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 41, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 41, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 42, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 42, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 43, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 43, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 44, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 44, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 36
- Run 45, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 45, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 46, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 46, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 47, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 47, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 48, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 48, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 49, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 49, reserved_matches_reservations fail: WIDGET reserved_quantity 24 but live reservations sum to 36
- Run 50, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 50, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 51, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 51, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 52, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 26
- Run 53, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 53, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 36
- Run 54, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 54, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 55, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 55, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
- Run 56, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 56, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 57, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 57, reserved_matches_reservations fail: WIDGET reserved_quantity 22 but live reservations sum to 31
- Run 58, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 58, reserved_matches_reservations fail: WIDGET reserved_quantity 26 but live reservations sum to 31
- Run 59, no_oversell fail: WIDGET live reservations 36 exceed stocked 26; WIDGET orders need 36 units but 26 were stocked at the start of the race
- Run 59, reserved_matches_reservations fail: WIDGET reserved_quantity 24 but live reservations sum to 36
- Run 60, no_oversell fail: WIDGET live reservations 31 exceed stocked 26; WIDGET orders need 31 units but 26 were stocked at the start of the race
- Run 60, reserved_matches_reservations fail: WIDGET reserved_quantity 23 but live reservations sum to 31
