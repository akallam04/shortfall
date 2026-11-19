# random-003-s1-pr-17420-control

- Scenario file: `random-003-s1-pr-17420-control.yaml`, sha256 `aff5ea68c1f8d363234de27c6591159fed3ceeb3548ae2bebe1c4c523641bef3`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Variant `pr-17420`: Medusa 2.22.0 with the source change of https://github.com/medusajs/medusa/pull/17420 by haranishi (closed, not merged), head commit `5332c04634e5e02ff05a5ef98a38d7c593205ee5`
  - Replaces `@medusajs/inventory/dist/services/inventory-module.js`, sha256 `3744f5fc9f893e4070be02c4a74f338c67c14c5099f97e9470776ccf8df1874b` (was `6d2643ef94e7ffe20fb2b4a35f8f1de503ad4429c85c64cc4262ceae2a776c58`)
- Server `medusa`: Medusa 2.22.0, image `sha256:e3bcacbc669133e02b8372ceccf0e7184623625404fdf274a5880f392805e29a`
  - Image inputs sha256 `47a24af91270797a42fcf8d465c9f25371b24cee68596902fef016ee7bc0af21`
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

- Run 1, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 2, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 3, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 4, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 5, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 6, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 7, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 8, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 9, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
- Run 10, no_oversell fail: WIDGET live reservations 6 exceed stocked 5; WIDGET orders need 6 units but 5 were stocked at the start of the race
