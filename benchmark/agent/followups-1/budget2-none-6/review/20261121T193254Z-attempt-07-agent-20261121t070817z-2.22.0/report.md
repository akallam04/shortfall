# attempt-07-agent-20261121t070817z

- Scenario file: `a-as-is.yaml`, sha256 `7a5faddc464338ad271639683283b2f30f91ce8f7ce07d695bf14df93671e2de`
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
| reserved_matches_reservations | 2 | 59 of 100 | 41 of 100 | 0 of 100 |
| one_order_per_cart | 2 | 4 of 100 | 96 of 100 | 0 of 100 |
| no_orphaned_orders | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_missing_orders | 1 | 0 of 100 | 100 of 100 | 0 of 100 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | fail | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | pass | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | fail | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | pass | pass | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | pass | pass | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | pass | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | fail | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | pass | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | pass | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | pass | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | fail | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | fail | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | pass | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | fail | fail | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | pass | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | fail | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | pass | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | pass | pass | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | fail | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | pass | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | pass | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | fail | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | fail | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | pass | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | fail | fail | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | pass | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | pass | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | fail | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | fail | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | fail | pass | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | fail | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | pass | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | fail | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | fail | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | fail | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | fail | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | fail | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | fail | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | fail | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | pass | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | fail | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | fail | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | fail | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | fail | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | fail | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | fail | pass | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | pass | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | fail | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | pass | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | fail | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | fail | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | fail | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | fail | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |
| 61 | pass | pass | pass | pass | pass | [run-061.json.gz](run-061.json.gz) |
| 62 | pass | pass | pass | pass | pass | [run-062.json.gz](run-062.json.gz) |
| 63 | pass | pass | pass | pass | pass | [run-063.json.gz](run-063.json.gz) |
| 64 | pass | fail | pass | pass | pass | [run-064.json.gz](run-064.json.gz) |
| 65 | pass | pass | pass | pass | pass | [run-065.json.gz](run-065.json.gz) |
| 66 | pass | fail | pass | pass | pass | [run-066.json.gz](run-066.json.gz) |
| 67 | pass | fail | pass | pass | pass | [run-067.json.gz](run-067.json.gz) |
| 68 | pass | fail | pass | pass | pass | [run-068.json.gz](run-068.json.gz) |
| 69 | pass | fail | pass | pass | pass | [run-069.json.gz](run-069.json.gz) |
| 70 | pass | fail | pass | pass | pass | [run-070.json.gz](run-070.json.gz) |
| 71 | pass | fail | pass | pass | pass | [run-071.json.gz](run-071.json.gz) |
| 72 | pass | fail | pass | pass | pass | [run-072.json.gz](run-072.json.gz) |
| 73 | pass | fail | pass | pass | pass | [run-073.json.gz](run-073.json.gz) |
| 74 | pass | fail | pass | pass | pass | [run-074.json.gz](run-074.json.gz) |
| 75 | pass | pass | pass | pass | pass | [run-075.json.gz](run-075.json.gz) |
| 76 | pass | pass | pass | pass | pass | [run-076.json.gz](run-076.json.gz) |
| 77 | pass | pass | pass | pass | pass | [run-077.json.gz](run-077.json.gz) |
| 78 | pass | pass | pass | pass | pass | [run-078.json.gz](run-078.json.gz) |
| 79 | pass | pass | pass | pass | pass | [run-079.json.gz](run-079.json.gz) |
| 80 | pass | fail | pass | pass | pass | [run-080.json.gz](run-080.json.gz) |
| 81 | pass | pass | pass | pass | pass | [run-081.json.gz](run-081.json.gz) |
| 82 | pass | pass | pass | pass | pass | [run-082.json.gz](run-082.json.gz) |
| 83 | pass | fail | pass | pass | pass | [run-083.json.gz](run-083.json.gz) |
| 84 | pass | fail | pass | pass | pass | [run-084.json.gz](run-084.json.gz) |
| 85 | pass | fail | fail | pass | pass | [run-085.json.gz](run-085.json.gz) |
| 86 | pass | fail | pass | pass | pass | [run-086.json.gz](run-086.json.gz) |
| 87 | pass | pass | pass | pass | pass | [run-087.json.gz](run-087.json.gz) |
| 88 | pass | pass | pass | pass | pass | [run-088.json.gz](run-088.json.gz) |
| 89 | pass | pass | pass | pass | pass | [run-089.json.gz](run-089.json.gz) |
| 90 | pass | fail | pass | pass | pass | [run-090.json.gz](run-090.json.gz) |
| 91 | pass | pass | pass | pass | pass | [run-091.json.gz](run-091.json.gz) |
| 92 | pass | fail | pass | pass | pass | [run-092.json.gz](run-092.json.gz) |
| 93 | pass | fail | pass | pass | pass | [run-093.json.gz](run-093.json.gz) |
| 94 | pass | fail | pass | pass | pass | [run-094.json.gz](run-094.json.gz) |
| 95 | pass | pass | pass | pass | pass | [run-095.json.gz](run-095.json.gz) |
| 96 | pass | fail | pass | pass | pass | [run-096.json.gz](run-096.json.gz) |
| 97 | pass | fail | fail | pass | pass | [run-097.json.gz](run-097.json.gz) |
| 98 | pass | fail | pass | pass | pass | [run-098.json.gz](run-098.json.gz) |
| 99 | pass | pass | pass | pass | pass | [run-099.json.gz](run-099.json.gz) |
| 100 | pass | fail | pass | pass | pass | [run-100.json.gz](run-100.json.gz) |

## Failed and inconclusive verdicts

- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 3, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 5, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 11, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 15, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 4
- Run 16, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 19, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 19, one_order_per_cart fail: cart piece-1 (cart_01M7ZSN869XT5CSGGM87N3GTTZ) is linked to 2 orders: order_01M7ZSN9N9G79F0Z22BG5P7ZF9, order_01M7ZSN9NANPJGQ0WMXQVDX85E; cart piece-1: ok complete calls returned 2 different orders (piece-on-2-1#43=order_01M7ZSN9NANPJGQ0WMXQVDX85E, piece-on-1-1#46=order_01M7ZSN9N9G79F0Z22BG5P7ZF9)
- Run 21, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 24, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 27, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 28, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 4
- Run 31, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 31, one_order_per_cart fail: cart piece-4 (cart_01M7ZSQGM0E820E8F4P89X4EQT) is linked to 2 orders: order_01M7ZSQH1SHHD90AQ8567EJB6P, order_01M7ZSQH2C3YMDDQG77MYSVTK9; cart piece-4: ok complete calls returned 2 different orders (piece-on-1-4#48=order_01M7ZSQH1SHHD90AQ8567EJB6P, piece-on-2-4#49=order_01M7ZSQH2C3YMDDQG77MYSVTK9)
- Run 34, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 35, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 36, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 37, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 39, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 40, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 41, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 42, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 43, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 44, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 45, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 47, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 48, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 49, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 4
- Run 50, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 51, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 52, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 54, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 57, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 58, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 59, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 60, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 64, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 66, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 67, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 68, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 69, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 70, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 71, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 72, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 73, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 74, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 80, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 83, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 84, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 85, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 85, one_order_per_cart fail: cart piece-3 (cart_01M7ZT1HW3645X0W8TYXYBSZ7F) is linked to 2 orders: order_01M7ZT1JJP1NYMVQCAJB7BP3SD, order_01M7ZT1JJS4K61Y9VJ6SNDBM4G; cart piece-3: ok complete calls returned 2 different orders (piece-on-2-3#44=order_01M7ZT1JJS4K61Y9VJ6SNDBM4G, piece-on-1-3#48=order_01M7ZT1JJP1NYMVQCAJB7BP3SD)
- Run 86, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 90, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 92, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 93, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 94, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 96, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 97, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 97, one_order_per_cart fail: cart piece-2 (cart_01M7ZT3RPA2F19Z6XS7WWW74AN) is linked to 2 orders: order_01M7ZT3SQ5N9CE08YHK7MY6JJ5, order_01M7ZT3SQPCYZ8MXCTE4PC98P8; cart piece-2: ok complete calls returned 2 different orders (piece-on-2-2#44=order_01M7ZT3SQPCYZ8MXCTE4PC98P8, piece-on-1-2#46=order_01M7ZT3SQ5N9CE08YHK7MY6JJ5)
- Run 98, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 4
- Run 100, reserved_matches_reservations fail: WIDGET reserved_quantity 1 but live reservations sum to 4
