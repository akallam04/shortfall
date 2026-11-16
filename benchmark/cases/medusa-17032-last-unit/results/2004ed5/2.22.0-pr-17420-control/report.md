# last-unit-two-servers-pr-17420-control

- Scenario file: `pr-17420-control.yaml`, sha256 `f8de47e5eee379d86c0ec603abf31d6978405e292a882c0bb4f2ad77c4dd7d41`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Variant `pr-17420`: Medusa 2.22.0 with the source change of https://github.com/medusajs/medusa/pull/17420 by haranishi (closed, not merged), head commit `5332c04634e5e02ff05a5ef98a38d7c593205ee5`
  - Replaces `@medusajs/inventory/dist/services/inventory-module.js`, sha256 `3744f5fc9f893e4070be02c4a74f338c67c14c5099f97e9470776ccf8df1874b` (was `6d2643ef94e7ffe20fb2b4a35f8f1de503ad4429c85c64cc4262ceae2a776c58`)
- Server `medusa`: Medusa 2.22.0, image `sha256:e3bcacbc669133e02b8372ceccf0e7184623625404fdf274a5880f392805e29a`
  - Image inputs sha256 `47a24af91270797a42fcf8d465c9f25371b24cee68596902fef016ee7bc0af21`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:e3bcacbc669133e02b8372ceccf0e7184623625404fdf274a5880f392805e29a`
  - Image inputs sha256 `47a24af91270797a42fcf8d465c9f25371b24cee68596902fef016ee7bc0af21`
- Postgres 15.19
- Locking: in-memory
- Runs: 30 of 30 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 30 | 30 of 30 | 0 of 30 |
| reserved_matches_reservations | 2 | 0 of 30 | 30 of 30 | 0 of 30 |
| one_order_per_cart | 2 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_orphaned_orders | 2 | 0 of 30 | 30 of 30 | 0 of 30 |
| no_missing_orders | 1 | 0 of 30 | 30 of 30 | 0 of 30 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
