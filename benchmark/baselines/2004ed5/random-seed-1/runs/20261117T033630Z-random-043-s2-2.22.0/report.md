# random-043-s2

- Scenario file: `random-043-s2.yaml`, sha256 `baec0ef53451780ccc72bc0ed8d196c4833a1c3c85898f6990c2a54c77e11795`
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
| no_oversell | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| reserved_matches_reservations | 2 | 10 of 10 | 0 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 32 but live reservations sum to 38
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 34 but live reservations sum to 38
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 30 but live reservations sum to 38
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 30 but live reservations sum to 38
