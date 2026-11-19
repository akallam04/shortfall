# random-062-s2

- Scenario file: `random-062-s2.yaml`, sha256 `32fea9eb1d1fd5be11a4ce65877b7705b8faafc401226e0abba722069b5465a3`
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
| no_oversell | 2 | 10 of 10 | 0 of 10 | 0 of 10 |
| reserved_matches_reservations | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | fail | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | fail | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | fail | pass | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | fail | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | fail | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | fail | pass | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | fail | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | fail | pass | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | fail | pass | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | fail | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |

## Failed and inconclusive verdicts

- Run 1, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 2, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 3, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 4, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 5, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 6, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 7, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 8, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 9, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
- Run 10, no_oversell fail: WIDGET live reservations 32 exceed stocked 31; WIDGET orders need 32 units but 31 were stocked at the start of the race
