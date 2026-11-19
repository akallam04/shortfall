# random-057-s2

- Scenario file: `random-057-s2.yaml`, sha256 `1c41deda94c76e22c665ada98e3dbb94025377cf4c1cb8ed5c7d072fe1cf4b44`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 1 of 1 recorded
- Exit code: 3

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 1 | 0 of 1 | 1 of 1 |
| reserved_matches_reservations | 2 | 0 of 1 | 0 of 1 | 1 of 1 |
| one_order_per_cart | 2 | 0 of 1 | 0 of 1 | 1 of 1 |
| no_orphaned_orders | 2 | 0 of 1 | 0 of 1 | 1 of 1 |
| no_missing_orders | 1 | 0 of 1 | 0 of 1 | 1 of 1 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | inconclusive | inconclusive | inconclusive | inconclusive | inconclusive | [run-001.json.gz](run-001.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell inconclusive: harness error: prepare cart buyer-a: add_line_item: outcome failed: http 400 not_allowed: Some variant does not have the required inventory
- Run 1, reserved_matches_reservations inconclusive: harness error: prepare cart buyer-a: add_line_item: outcome failed: http 400 not_allowed: Some variant does not have the required inventory
- Run 1, one_order_per_cart inconclusive: harness error: prepare cart buyer-a: add_line_item: outcome failed: http 400 not_allowed: Some variant does not have the required inventory
- Run 1, no_orphaned_orders inconclusive: harness error: prepare cart buyer-a: add_line_item: outcome failed: http 400 not_allowed: Some variant does not have the required inventory
- Run 1, no_missing_orders inconclusive: harness error: prepare cart buyer-a: add_line_item: outcome failed: http 400 not_allowed: Some variant does not have the required inventory
