# attempt-01-agent-20261117t174816z-pr-16961-control

- Scenario file: `attempt-01-pr-16961-control.yaml`, sha256 `180de6d954e8fe6f28b3c123b726f0ecdf77002b7cfe76c8518a425731999595`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Variant `pr-16961`: Medusa 2.22.0 with the source change of https://github.com/medusajs/medusa/pull/16961 by pqa-labs (closed, not merged), head commit `5ac8ae437ee0b7771a945b5b30f265b76f214172`
  - Replaces `@medusajs/inventory/dist/services/inventory-module.js`, sha256 `8e150f6b9de7bc64f431e91a803716646a782379d3cc993a31f301056d5ac919` (was `6d2643ef94e7ffe20fb2b4a35f8f1de503ad4429c85c64cc4262ceae2a776c58`)
  - Replaces `@medusajs/core-flows/dist/cart/steps/confirm-inventory.js`, sha256 `2af8432c719836364a143d9fe7f4ee6f9aba17062d555e2fdace47315c11c569` (was `01a7cf229b6854a7840207c6ba62234bbdedc651adfd50276536e06d6e46134d`)
- Server `medusa`: Medusa 2.22.0, image `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`
  - Image inputs sha256 `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
- Postgres 15.19
- Locking: in-memory
- Runs: 10 of 10 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| reserved_matches_reservations | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| one_order_per_cart | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_orphaned_orders | 2 | 0 of 10 | 10 of 10 | 0 of 10 |
| no_missing_orders | 1 | 0 of 10 | 10 of 10 | 0 of 10 |

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
