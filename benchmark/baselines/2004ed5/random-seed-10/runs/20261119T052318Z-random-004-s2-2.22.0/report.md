# random-004-s2

- Scenario file: `random-004-s2.yaml`, sha256 `ba93d495bda193e8c768a70238b7c72e40adbd109b9aad7bdab9754f0604eddc`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 2 of 2 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 1 of 2 | 1 of 2 | 0 of 2 |
| reserved_matches_reservations | 2 | 1 of 2 | 1 of 2 | 0 of 2 |
| one_order_per_cart | 2 | 0 of 2 | 2 of 2 | 0 of 2 |
| no_orphaned_orders | 2 | 0 of 2 | 2 of 2 | 0 of 2 |
| no_missing_orders | 1 | 0 of 2 | 2 of 2 | 0 of 2 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | fail | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |

## Failed and inconclusive verdicts

- Run 2, no_oversell fail: WIDGET live reservations 23 exceed stocked 19; WIDGET orders need 23 units but 19 were stocked at the start of the race
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 19 but live reservations sum to 23
