# grid-010-s2-piece-twopack-c2-short-together

- Scenario file: `grid-010-s2-piece-twopack-c2-short-together.yaml`, sha256 `4ee4fc73daafb53e7810d7996744ffd93c2391b877b91058b58d8189255a7236`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 10 of 10 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 7 of 10 | 3 of 10 | 0 of 10 |
| reserved_matches_reservations | 2 | 7 of 10 | 3 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | fail | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | fail | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | fail | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | fail | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | fail | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |

## Failed and inconclusive verdicts

- Run 3, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 4, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 5, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 6, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 7, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 8, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
- Run 9, no_oversell fail: WIDGET live reservations 6 exceed stocked 3; WIDGET orders need 6 units but 3 were stocked at the start of the race
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 6
