# random-045-s2-pr-16961-control-redis-control

- Scenario file: `random-045-s2-pr-16961-redis-control.yaml`, sha256 `04944d48e5d80a66f68d19ff2746a62b390d87556f852a7c9e85b07af0201553`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Variant `pr-16961`: Medusa 2.22.0 with the source change of https://github.com/medusajs/medusa/pull/16961 by pqa-labs (closed, not merged), head commit `5ac8ae437ee0b7771a945b5b30f265b76f214172`
  - Replaces `@medusajs/inventory/dist/services/inventory-module.js`, sha256 `8e150f6b9de7bc64f431e91a803716646a782379d3cc993a31f301056d5ac919` (was `6d2643ef94e7ffe20fb2b4a35f8f1de503ad4429c85c64cc4262ceae2a776c58`)
  - Replaces `@medusajs/core-flows/dist/cart/steps/confirm-inventory.js`, sha256 `2af8432c719836364a143d9fe7f4ee6f9aba17062d555e2fdace47315c11c569` (was `01a7cf229b6854a7840207c6ba62234bbdedc651adfd50276536e06d6e46134d`)
- Server `medusa`: Medusa 2.22.0, image `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`
  - Image inputs sha256 `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:0075cea17c12ad8e6db26908d310d823cad73216547ab3a6f05042a001e82a9c`
  - Image inputs sha256 `ee262621f93e2ba8e44d0e7d090c616f40ad572fe2c2c8706cdd0cb01e5e6ae5`
- Postgres 15.19
- Locking: redis
- Redis 7.4.11
- Scripted Redis lock calls during the race: 128 to 139 per run, recorded in 60 runs
- Runs: 60 of 60 recorded
- Exit code: 0

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| reserved_matches_reservations | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| one_order_per_cart | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_orphaned_orders | 2 | 0 of 60 | 60 of 60 | 0 of 60 |
| no_missing_orders | 1 | 0 of 60 | 60 of 60 | 0 of 60 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | Lock calls | History |
|---|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | 139 | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | 139 | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | 135 | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | 139 | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | 132 | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | 130 | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | 131 | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | pass | 138 | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | 135 | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | 134 | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | pass | 134 | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | pass | 131 | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | 135 | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | 138 | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | pass | 128 | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | pass | 135 | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | pass | 128 | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | 139 | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | pass | 137 | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | pass | 132 | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | pass | 134 | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | 138 | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | pass | 133 | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | pass | 134 | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | 130 | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | pass | 134 | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | pass | pass | pass | 139 | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | pass | 134 | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | 136 | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | pass | 138 | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | pass | pass | pass | pass | 139 | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | 134 | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | 134 | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | pass | pass | pass | pass | 132 | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | 133 | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | pass | pass | pass | pass | 129 | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | pass | pass | pass | pass | 130 | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | 136 | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | pass | pass | pass | pass | 131 | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | pass | pass | pass | pass | 133 | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | pass | pass | pass | pass | 138 | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | pass | pass | pass | pass | 131 | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | pass | pass | pass | pass | 129 | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | 134 | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | pass | pass | pass | pass | 133 | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | 136 | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | pass | pass | pass | pass | 132 | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | pass | pass | pass | pass | 134 | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | pass | pass | pass | pass | 132 | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | pass | pass | pass | pass | 133 | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | pass | pass | pass | pass | 132 | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | pass | pass | pass | pass | 134 | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | pass | pass | pass | pass | 133 | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | pass | pass | pass | pass | 136 | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | 134 | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | 132 | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | pass | pass | pass | pass | 133 | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | pass | pass | pass | pass | 131 | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | pass | pass | pass | pass | 134 | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | pass | pass | pass | pass | 135 | [run-060.json.gz](run-060.json.gz) |
