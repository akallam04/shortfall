# attempt-07-agent-20261121t070817z-pr-17420

- Scenario file: `d-pr-17420.yaml`, sha256 `ec84f07f510fe52da60921214cca5be2e44a925f22d8181786a294f8e105e714`
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
- Runs: 100 of 100 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| reserved_matches_reservations | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| one_order_per_cart | 2 | 2 of 100 | 98 of 100 | 0 of 100 |
| no_orphaned_orders | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_missing_orders | 1 | 0 of 100 | 100 of 100 | 0 of 100 |

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
| 31 | pass | pass | pass | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | pass | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | pass | pass | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | pass | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | pass | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | pass | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | pass | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | pass | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | pass | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | pass | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | pass | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | pass | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | pass | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | pass | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | pass | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | pass | fail | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | pass | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | pass | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | pass | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | pass | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | pass | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | pass | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |
| 61 | pass | pass | pass | pass | pass | [run-061.json.gz](run-061.json.gz) |
| 62 | pass | pass | pass | pass | pass | [run-062.json.gz](run-062.json.gz) |
| 63 | pass | pass | pass | pass | pass | [run-063.json.gz](run-063.json.gz) |
| 64 | pass | pass | pass | pass | pass | [run-064.json.gz](run-064.json.gz) |
| 65 | pass | pass | pass | pass | pass | [run-065.json.gz](run-065.json.gz) |
| 66 | pass | pass | pass | pass | pass | [run-066.json.gz](run-066.json.gz) |
| 67 | pass | pass | pass | pass | pass | [run-067.json.gz](run-067.json.gz) |
| 68 | pass | pass | pass | pass | pass | [run-068.json.gz](run-068.json.gz) |
| 69 | pass | pass | pass | pass | pass | [run-069.json.gz](run-069.json.gz) |
| 70 | pass | pass | pass | pass | pass | [run-070.json.gz](run-070.json.gz) |
| 71 | pass | pass | pass | pass | pass | [run-071.json.gz](run-071.json.gz) |
| 72 | pass | pass | pass | pass | pass | [run-072.json.gz](run-072.json.gz) |
| 73 | pass | pass | fail | pass | pass | [run-073.json.gz](run-073.json.gz) |
| 74 | pass | pass | pass | pass | pass | [run-074.json.gz](run-074.json.gz) |
| 75 | pass | pass | pass | pass | pass | [run-075.json.gz](run-075.json.gz) |
| 76 | pass | pass | pass | pass | pass | [run-076.json.gz](run-076.json.gz) |
| 77 | pass | pass | pass | pass | pass | [run-077.json.gz](run-077.json.gz) |
| 78 | pass | pass | pass | pass | pass | [run-078.json.gz](run-078.json.gz) |
| 79 | pass | pass | pass | pass | pass | [run-079.json.gz](run-079.json.gz) |
| 80 | pass | pass | pass | pass | pass | [run-080.json.gz](run-080.json.gz) |
| 81 | pass | pass | pass | pass | pass | [run-081.json.gz](run-081.json.gz) |
| 82 | pass | pass | pass | pass | pass | [run-082.json.gz](run-082.json.gz) |
| 83 | pass | pass | pass | pass | pass | [run-083.json.gz](run-083.json.gz) |
| 84 | pass | pass | pass | pass | pass | [run-084.json.gz](run-084.json.gz) |
| 85 | pass | pass | pass | pass | pass | [run-085.json.gz](run-085.json.gz) |
| 86 | pass | pass | pass | pass | pass | [run-086.json.gz](run-086.json.gz) |
| 87 | pass | pass | pass | pass | pass | [run-087.json.gz](run-087.json.gz) |
| 88 | pass | pass | pass | pass | pass | [run-088.json.gz](run-088.json.gz) |
| 89 | pass | pass | pass | pass | pass | [run-089.json.gz](run-089.json.gz) |
| 90 | pass | pass | pass | pass | pass | [run-090.json.gz](run-090.json.gz) |
| 91 | pass | pass | pass | pass | pass | [run-091.json.gz](run-091.json.gz) |
| 92 | pass | pass | pass | pass | pass | [run-092.json.gz](run-092.json.gz) |
| 93 | pass | pass | pass | pass | pass | [run-093.json.gz](run-093.json.gz) |
| 94 | pass | pass | pass | pass | pass | [run-094.json.gz](run-094.json.gz) |
| 95 | pass | pass | pass | pass | pass | [run-095.json.gz](run-095.json.gz) |
| 96 | pass | pass | pass | pass | pass | [run-096.json.gz](run-096.json.gz) |
| 97 | pass | pass | pass | pass | pass | [run-097.json.gz](run-097.json.gz) |
| 98 | pass | pass | pass | pass | pass | [run-098.json.gz](run-098.json.gz) |
| 99 | pass | pass | pass | pass | pass | [run-099.json.gz](run-099.json.gz) |
| 100 | pass | pass | pass | pass | pass | [run-100.json.gz](run-100.json.gz) |

## Failed and inconclusive verdicts

- Run 52, one_order_per_cart fail: cart piece-2 (cart_01M7ZVPSBHKHY0CJP2GPAR92CX) is linked to 2 orders: order_01M7ZVPTS7ZDQ51VB7E1NSSW2E, order_01M7ZVPTSGBW922Y265PWK7FYS; cart piece-2: ok complete calls returned 2 different orders (piece-on-2-2#44=order_01M7ZVPTSGBW922Y265PWK7FYS, piece-on-1-2#49=order_01M7ZVPTS7ZDQ51VB7E1NSSW2E)
- Run 73, one_order_per_cart fail: cart piece-1 (cart_01M7ZVTXQ0JTDPT5KMVK7YQPCZ) is linked to 2 orders: order_01M7ZVTZCZR5SN5D6J6QPNTXMJ, order_01M7ZVTZE2QB4ZVMZQ95XWYJXX; cart piece-1: ok complete calls returned 2 different orders (piece-on-1-1#44=order_01M7ZVTZCZR5SN5D6J6QPNTXMJ, piece-on-2-1#47=order_01M7ZVTZE2QB4ZVMZQ95XWYJXX)
