# attempt-12-agent-20261121t070817z

- Scenario file: `a-as-is.yaml`, sha256 `0e959e2ce2d9a004433c303597dbb3478ee747d115e82cf6c88514f71f8a657a`
- Medusa version in the file: 2.22.0. Version used: 2.22.0
- Oversold commit that ran it: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Verdicts computed by Oversold commit: `2004ed534b765a3b3341efaadb3f352ffdecef90` (clean)
- Server `medusa`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Server `medusa-2`: Medusa 2.22.0, image `sha256:c48358f78c193ccba70f4a7bf5e1e0048decb55bf4019cec48cc631658da0527`
  - Image inputs sha256 `d701e53cf957c292585cdcafdd628b75a330047e838f35c985b7534153b72be5`
- Postgres 15.19
- Locking: in-memory
- Runs: 100 of 100 recorded
- Exit code: 1

## Checks

| Check | Version | Fail | Pass | Inconclusive |
|---|---|---|---|---|
| no_oversell | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| reserved_matches_reservations | 2 | 28 of 100 | 72 of 100 | 0 of 100 |
| one_order_per_cart | 2 | 6 of 100 | 94 of 100 | 0 of 100 |
| no_orphaned_orders | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_missing_orders | 1 | 0 of 100 | 100 of 100 | 0 of 100 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | pass | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | pass | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | pass | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | pass | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | pass | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | pass | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | fail | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | pass | pass | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | pass | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | fail | fail | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | pass | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | fail | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | pass | fail | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | pass | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | fail | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | fail | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | pass | pass | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | pass | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | fail | fail | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | pass | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | pass | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | fail | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | pass | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | pass | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | pass | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | pass | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | fail | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | fail | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | fail | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | fail | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | fail | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | fail | pass | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | fail | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | pass | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | pass | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | pass | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | fail | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | fail | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |
| 61 | pass | pass | pass | pass | pass | [run-061.json.gz](run-061.json.gz) |
| 62 | pass | pass | pass | pass | pass | [run-062.json.gz](run-062.json.gz) |
| 63 | pass | pass | pass | pass | pass | [run-063.json.gz](run-063.json.gz) |
| 64 | pass | fail | pass | pass | pass | [run-064.json.gz](run-064.json.gz) |
| 65 | pass | pass | pass | pass | pass | [run-065.json.gz](run-065.json.gz) |
| 66 | pass | pass | pass | pass | pass | [run-066.json.gz](run-066.json.gz) |
| 67 | pass | fail | pass | pass | pass | [run-067.json.gz](run-067.json.gz) |
| 68 | pass | fail | pass | pass | pass | [run-068.json.gz](run-068.json.gz) |
| 69 | pass | pass | pass | pass | pass | [run-069.json.gz](run-069.json.gz) |
| 70 | pass | pass | pass | pass | pass | [run-070.json.gz](run-070.json.gz) |
| 71 | pass | pass | pass | pass | pass | [run-071.json.gz](run-071.json.gz) |
| 72 | pass | pass | pass | pass | pass | [run-072.json.gz](run-072.json.gz) |
| 73 | pass | pass | pass | pass | pass | [run-073.json.gz](run-073.json.gz) |
| 74 | pass | pass | pass | pass | pass | [run-074.json.gz](run-074.json.gz) |
| 75 | pass | pass | pass | pass | pass | [run-075.json.gz](run-075.json.gz) |
| 76 | pass | fail | fail | pass | pass | [run-076.json.gz](run-076.json.gz) |
| 77 | pass | pass | pass | pass | pass | [run-077.json.gz](run-077.json.gz) |
| 78 | pass | pass | pass | pass | pass | [run-078.json.gz](run-078.json.gz) |
| 79 | pass | pass | pass | pass | pass | [run-079.json.gz](run-079.json.gz) |
| 80 | pass | pass | pass | pass | pass | [run-080.json.gz](run-080.json.gz) |
| 81 | pass | pass | pass | pass | pass | [run-081.json.gz](run-081.json.gz) |
| 82 | pass | pass | pass | pass | pass | [run-082.json.gz](run-082.json.gz) |
| 83 | pass | pass | pass | pass | pass | [run-083.json.gz](run-083.json.gz) |
| 84 | pass | fail | pass | pass | pass | [run-084.json.gz](run-084.json.gz) |
| 85 | pass | fail | pass | pass | pass | [run-085.json.gz](run-085.json.gz) |
| 86 | pass | pass | pass | pass | pass | [run-086.json.gz](run-086.json.gz) |
| 87 | pass | pass | pass | pass | pass | [run-087.json.gz](run-087.json.gz) |
| 88 | pass | pass | pass | pass | pass | [run-088.json.gz](run-088.json.gz) |
| 89 | pass | pass | pass | pass | pass | [run-089.json.gz](run-089.json.gz) |
| 90 | pass | pass | pass | pass | pass | [run-090.json.gz](run-090.json.gz) |
| 91 | pass | pass | pass | pass | pass | [run-091.json.gz](run-091.json.gz) |
| 92 | pass | pass | pass | pass | pass | [run-092.json.gz](run-092.json.gz) |
| 93 | pass | pass | pass | pass | pass | [run-093.json.gz](run-093.json.gz) |
| 94 | pass | fail | fail | pass | pass | [run-094.json.gz](run-094.json.gz) |
| 95 | pass | pass | pass | pass | pass | [run-095.json.gz](run-095.json.gz) |
| 96 | pass | pass | pass | pass | pass | [run-096.json.gz](run-096.json.gz) |
| 97 | pass | fail | pass | pass | pass | [run-097.json.gz](run-097.json.gz) |
| 98 | pass | fail | pass | pass | pass | [run-098.json.gz](run-098.json.gz) |
| 99 | pass | pass | pass | pass | pass | [run-099.json.gz](run-099.json.gz) |
| 100 | pass | fail | fail | pass | pass | [run-100.json.gz](run-100.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 17, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 23, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 23, one_order_per_cart fail: cart dup-2 (cart_01M7ZW4VDXH9M8P3EQF1VV13C5) is linked to 2 orders: order_01M7ZW4W5G6N01BQ6910ZGRP82, order_01M7ZW4W63CAM3YHK9437MBW0G; cart dup-2: ok complete calls returned 2 different orders (dup-on-2-2#33=order_01M7ZW4W63CAM3YHK9437MBW0G, dup-on-1-2#35=order_01M7ZW4W5G6N01BQ6910ZGRP82)
- Run 26, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 27, one_order_per_cart fail: cart dup-2 (cart_01M7ZW5J68BJJW42Y2MW0R378B) is linked to 2 orders: order_01M7ZW5JXQ1PWBENE5ZYQ7PX0X, order_01M7ZW5JYAMZ43W69VSDS8MZ4F; cart dup-2: ok complete calls returned 2 different orders (dup-on-2-2#34=order_01M7ZW5JYAMZ43W69VSDS8MZ4F, dup-on-1-2#36=order_01M7ZW5JXQ1PWBENE5ZYQ7PX0X)
- Run 29, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 30, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 36, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 36, one_order_per_cart fail: cart dup-1 (cart_01M7ZW74TMENXS3G0P5YS2QF5F) is linked to 2 orders: order_01M7ZW75ZK9RAQ5NM62AMPZZJE, order_01M7ZW760A8BBM31XV73XZKW48; cart dup-1: ok complete calls returned 2 different orders (dup-on-2-1#33=order_01M7ZW760A8BBM31XV73XZKW48, dup-on-1-1#37=order_01M7ZW75ZK9RAQ5NM62AMPZZJE)
- Run 40, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 47, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 48, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 49, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 50, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 51, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 52, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 53, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 59, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 60, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 64, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 67, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 68, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 76, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 4
- Run 76, one_order_per_cart fail: cart dup-1 (cart_01M7ZWE860FND93KD3X0QG98K7) is linked to 2 orders: order_01M7ZWE9BN75FPJ49BTQV7DZ8A, order_01M7ZWE9BPESADXCARVD7K65YQ; cart dup-1: ok complete calls returned 2 different orders (dup-on-1-1#33=order_01M7ZWE9BN75FPJ49BTQV7DZ8A, dup-on-2-1#34=order_01M7ZWE9BPESADXCARVD7K65YQ)
- Run 84, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 85, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 94, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 94, one_order_per_cart fail: cart dup-2 (cart_01M7ZWHFEX00RQRE26YW6EGNJD) is linked to 2 orders: order_01M7ZWHG726BXKASG66TVDREEY, order_01M7ZWHG74ENDC2J5V685C2R3X; cart dup-2: ok complete calls returned 2 different orders (dup-on-2-2#36=order_01M7ZWHG74ENDC2J5V685C2R3X, dup-on-1-2#38=order_01M7ZWHG726BXKASG66TVDREEY)
- Run 97, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 98, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 3
- Run 100, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 100, one_order_per_cart fail: cart dup-1 (cart_01M7ZWJHQ4EYBZ7MD9PS9HP3F0) is linked to 2 orders: order_01M7ZWJJZ3EKTBD77VPMH1VV4H, order_01M7ZWJJZRW399Y872GC3Z77GB; cart dup-2 (cart_01M7ZWJJ59FZ9D5SSQ1RGN9GMB) is linked to 2 orders: order_01M7ZWJJZ59WW55FKQ7100MM0F, order_01M7ZWJJZRW3CG9GZS04BP51GW; cart dup-1: ok complete calls returned 2 different orders (dup-on-1-1#35=order_01M7ZWJJZ3EKTBD77VPMH1VV4H, dup-on-2-1#38=order_01M7ZWJJZRW399Y872GC3Z77GB); cart dup-2: ok complete calls returned 2 different orders (dup-on-1-2#34=order_01M7ZWJJZRW3CG9GZS04BP51GW, dup-on-2-2#36=order_01M7ZWJJZ59WW55FKQ7100MM0F)
