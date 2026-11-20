# attempt-06-agent-20261120t055627z

- Scenario file: `attempt-06.yaml`, sha256 `667e4053dcb7c3a8ce30d22cb6488829be8bfdb4be3a6486292d0b768d4cbebc`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 1 of 1 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| reserved_matches_reservations | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| one_order_per_cart | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| no_orphaned_orders | 2 | 0 of 1 | 1 of 1 | 0 of 1 |
| no_missing_orders | 1 | 0 of 1 | 1 of 1 | 0 of 1 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
