# attempt-03-agent-20261121t025734z

- Scenario file: `attempt-03.yaml`, sha256 `5982e9b01fa3ee854b3cdeaefd74b1fb5090038b840b6823d9eb8fb84378c5c7`
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
| reserved_matches_reservations | 2 | 9 of 10 | 1 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 1 of 10 | 9 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | fail | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 6
- Run 2, one_order_per_cart fail: cart c-3 (cart_01M7Y12D0M25NKPRKKNM3M4V6Y) is linked to 2 orders: order_01M7Y12E2ZDTWXVKMKMP28WKTT, order_01M7Y12E40CTHXTGCP7FPNZFRP; cart c-3: ok complete calls returned 2 different orders (r1-3#61=order_01M7Y12E40CTHXTGCP7FPNZFRP, r3-3#74=order_01M7Y12E40CTHXTGCP7FPNZFRP, r2-3#75=order_01M7Y12E2ZDTWXVKMKMP28WKTT, r4-3#80=order_01M7Y12E40CTHXTGCP7FPNZFRP)
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
