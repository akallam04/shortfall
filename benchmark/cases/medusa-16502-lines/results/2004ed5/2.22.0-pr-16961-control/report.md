# single-cart-over-demand-pr-16961-control

- Scenario file: `pr-16961-control.yaml`, sha256 `f88da01ee62c6fce8239f26561adbd57ed5908ad4ac462a1d61b0bb4be68944a`
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
