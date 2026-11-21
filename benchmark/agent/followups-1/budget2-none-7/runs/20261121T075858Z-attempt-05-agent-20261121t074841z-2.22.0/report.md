# attempt-05-agent-20261121t074841z

- Scenario file: `attempt-05.yaml`, sha256 `7c224875b79d0925e00c7c92579b0a8f42f04b939d7e07de0c0abb6544bde58d`
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
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 1 of 1 | 0 of 1 | 0 of 1 |
| reserved_matches_reservations | 2 | 1 of 1 | 0 of 1 | 0 of 1 |
| one_order_per_cart | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| no_orphaned_orders | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| no_missing_orders | 1 | 0 of 1 | 1 of 1 | 0 of 1 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | fail | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: SOLO live reservations 2 exceed stocked 1; SOLO orders need 2 units but 1 were stocked at the start of the race
- Run 1, reserved_matches_reservations fail: SOLO reserved_quantity 1 but live reservations sum to 2
