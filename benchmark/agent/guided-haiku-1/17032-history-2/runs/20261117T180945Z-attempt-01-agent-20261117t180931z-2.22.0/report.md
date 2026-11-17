# attempt-01-agent-20261117t180931z

- Scenario file: `attempt-01.yaml`, sha256 `bd849b6d67c9862476ccef556ed52631836298bb15681b39d6d5f0ea5a77e450`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 2 of 2 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 1 of 2 | 1 of 2 | 0 of 2 |
| reserved_matches_reservations | 2 | 0 of 2 | 2 of 2 | 0 of 2 |
| one_order_per_cart | 2 | 0 of 2 | 2 of 2 | 0 of 2 |
| no_orphaned_orders | 2 | 0 of 2 | 2 of 2 | 0 of 2 |
| no_missing_orders | 1 | 0 of 2 | 2 of 2 | 0 of 2 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | fail | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 12 exceed stocked 10; WIDGET orders need 12 units but 10 were stocked at the start of the race
