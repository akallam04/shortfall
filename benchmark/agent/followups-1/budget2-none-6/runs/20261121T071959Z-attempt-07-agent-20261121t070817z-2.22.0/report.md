# attempt-07-agent-20261121t070817z

- Scenario file: `attempt-07.yaml`, sha256 `7a5faddc464338ad271639683283b2f30f91ce8f7ce07d695bf14df93671e2de`
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
| reserved_matches_reservations | 2 | 4 of 10 | 6 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 2 of 10 | 8 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | fail | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | fail | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 6, one_order_per_cart fail: cart piece-3 (cart_01M7YFMVGS6R6R27B32BK8JF2R) is linked to 2 orders: order_01M7YFMW75AT534JQ9Q2XBMPJW, order_01M7YFMW7V9AG4AKG3AE8VJSC6; cart piece-3: ok complete calls returned 2 different orders (piece-on-1-3#45=order_01M7YFMW75AT534JQ9Q2XBMPJW, piece-on-2-3#47=order_01M7YFMW7V9AG4AKG3AE8VJSC6)
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 9, one_order_per_cart fail: cart piece-2 (cart_01M7YFNCY2KXNB42NANDQ6Q11N) is linked to 2 orders: order_01M7YFNDYJEQVSTZV9QAAZVKQG, order_01M7YFNDYKW84G001S11ZNHAFB; cart piece-2: ok complete calls returned 2 different orders (piece-on-2-2#42=order_01M7YFNDYJEQVSTZV9QAAZVKQG, piece-on-1-2#48=order_01M7YFNDYKW84G001S11ZNHAFB)
