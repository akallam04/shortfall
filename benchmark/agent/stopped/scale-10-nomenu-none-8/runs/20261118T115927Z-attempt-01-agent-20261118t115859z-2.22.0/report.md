# attempt-01-agent-20261118t115859z

- Scenario file: `attempt-01.yaml`, sha256 `cfdafc98d3f2b9e00d7af025294f863b74581530b33342d86b1fcfb2f94baf80`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 7 of 7 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 1 of 7 | 6 of 7 | 0 of 7 |
| reserved_matches_reservations | 2 | 1 of 7 | 6 of 7 | 0 of 7 |
| one_order_per_cart | 2 | 1 of 7 | 6 of 7 | 0 of 7 |
| no_orphaned_orders | 2 | 0 of 7 | 7 of 7 | 0 of 7 |
| no_missing_orders | 1 | 0 of 7 | 7 of 7 | 0 of 7 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | fail | fail | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |

## Failed and inconclusive verdicts

- Run 3, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 3, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
- Run 3, one_order_per_cart fail: cart alice (cart_01M7Q8DRW6NZTNE2WFYQZ7TBWW) is linked to 2 orders: order_01M7Q8DSAXHT5EPJ8H0Y88GB1A, order_01M7Q8DSBWGED1SKVB1PR5VV6D; cart alice: ok complete calls returned 2 different orders (alice-complete-s2#15=order_01M7Q8DSBWGED1SKVB1PR5VV6D, alice-complete-s1#16=order_01M7Q8DSAXHT5EPJ8H0Y88GB1A)
