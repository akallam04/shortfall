# attempt-02-agent-20261120t072353z

- Scenario file: `a-as-is.yaml`, sha256 `e8a0adba215c8c84809a11b7e4a5abc66959d1a43bf632f9081f19ba4e778e1d`
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
| reserved_matches_reservations | 2 | 84 of 100 | 16 of 100 | 0 of 100 |
| one_order_per_cart | 2 | 4 of 100 | 96 of 100 | 0 of 100 |
| no_orphaned_orders | 2 | 0 of 100 | 100 of 100 | 0 of 100 |
| no_missing_orders | 1 | 0 of 100 | 100 of 100 | 0 of 100 |

## Runs

| Run | no_oversell | reserved_matches_reservations | one_order_per_cart | no_orphaned_orders | no_missing_orders | History |
|---|---|---|---|---|---|---|
| 1 | pass | fail | pass | pass | pass | [run-001.json.gz](run-001.json.gz) |
| 2 | pass | fail | pass | pass | pass | [run-002.json.gz](run-002.json.gz) |
| 3 | pass | pass | pass | pass | pass | [run-003.json.gz](run-003.json.gz) |
| 4 | pass | fail | pass | pass | pass | [run-004.json.gz](run-004.json.gz) |
| 5 | pass | pass | pass | pass | pass | [run-005.json.gz](run-005.json.gz) |
| 6 | pass | fail | pass | pass | pass | [run-006.json.gz](run-006.json.gz) |
| 7 | pass | fail | fail | pass | pass | [run-007.json.gz](run-007.json.gz) |
| 8 | pass | fail | fail | pass | pass | [run-008.json.gz](run-008.json.gz) |
| 9 | pass | fail | pass | pass | pass | [run-009.json.gz](run-009.json.gz) |
| 10 | pass | fail | pass | pass | pass | [run-010.json.gz](run-010.json.gz) |
| 11 | pass | fail | pass | pass | pass | [run-011.json.gz](run-011.json.gz) |
| 12 | pass | fail | pass | pass | pass | [run-012.json.gz](run-012.json.gz) |
| 13 | pass | fail | pass | pass | pass | [run-013.json.gz](run-013.json.gz) |
| 14 | pass | fail | pass | pass | pass | [run-014.json.gz](run-014.json.gz) |
| 15 | pass | fail | pass | pass | pass | [run-015.json.gz](run-015.json.gz) |
| 16 | pass | fail | pass | pass | pass | [run-016.json.gz](run-016.json.gz) |
| 17 | pass | fail | pass | pass | pass | [run-017.json.gz](run-017.json.gz) |
| 18 | pass | pass | pass | pass | pass | [run-018.json.gz](run-018.json.gz) |
| 19 | pass | fail | fail | pass | pass | [run-019.json.gz](run-019.json.gz) |
| 20 | pass | fail | pass | pass | pass | [run-020.json.gz](run-020.json.gz) |
| 21 | pass | fail | pass | pass | pass | [run-021.json.gz](run-021.json.gz) |
| 22 | pass | fail | pass | pass | pass | [run-022.json.gz](run-022.json.gz) |
| 23 | pass | fail | fail | pass | pass | [run-023.json.gz](run-023.json.gz) |
| 24 | pass | fail | pass | pass | pass | [run-024.json.gz](run-024.json.gz) |
| 25 | pass | fail | pass | pass | pass | [run-025.json.gz](run-025.json.gz) |
| 26 | pass | fail | pass | pass | pass | [run-026.json.gz](run-026.json.gz) |
| 27 | pass | fail | pass | pass | pass | [run-027.json.gz](run-027.json.gz) |
| 28 | pass | fail | pass | pass | pass | [run-028.json.gz](run-028.json.gz) |
| 29 | pass | pass | pass | pass | pass | [run-029.json.gz](run-029.json.gz) |
| 30 | pass | fail | pass | pass | pass | [run-030.json.gz](run-030.json.gz) |
| 31 | pass | fail | pass | pass | pass | [run-031.json.gz](run-031.json.gz) |
| 32 | pass | fail | pass | pass | pass | [run-032.json.gz](run-032.json.gz) |
| 33 | pass | fail | pass | pass | pass | [run-033.json.gz](run-033.json.gz) |
| 34 | pass | fail | pass | pass | pass | [run-034.json.gz](run-034.json.gz) |
| 35 | pass | pass | pass | pass | pass | [run-035.json.gz](run-035.json.gz) |
| 36 | pass | fail | pass | pass | pass | [run-036.json.gz](run-036.json.gz) |
| 37 | pass | fail | pass | pass | pass | [run-037.json.gz](run-037.json.gz) |
| 38 | pass | fail | pass | pass | pass | [run-038.json.gz](run-038.json.gz) |
| 39 | pass | fail | pass | pass | pass | [run-039.json.gz](run-039.json.gz) |
| 40 | pass | fail | pass | pass | pass | [run-040.json.gz](run-040.json.gz) |
| 41 | pass | pass | pass | pass | pass | [run-041.json.gz](run-041.json.gz) |
| 42 | pass | fail | pass | pass | pass | [run-042.json.gz](run-042.json.gz) |
| 43 | pass | fail | pass | pass | pass | [run-043.json.gz](run-043.json.gz) |
| 44 | pass | pass | pass | pass | pass | [run-044.json.gz](run-044.json.gz) |
| 45 | pass | fail | pass | pass | pass | [run-045.json.gz](run-045.json.gz) |
| 46 | pass | fail | pass | pass | pass | [run-046.json.gz](run-046.json.gz) |
| 47 | pass | fail | pass | pass | pass | [run-047.json.gz](run-047.json.gz) |
| 48 | pass | pass | pass | pass | pass | [run-048.json.gz](run-048.json.gz) |
| 49 | pass | fail | pass | pass | pass | [run-049.json.gz](run-049.json.gz) |
| 50 | pass | fail | pass | pass | pass | [run-050.json.gz](run-050.json.gz) |
| 51 | pass | fail | pass | pass | pass | [run-051.json.gz](run-051.json.gz) |
| 52 | pass | fail | pass | pass | pass | [run-052.json.gz](run-052.json.gz) |
| 53 | pass | fail | pass | pass | pass | [run-053.json.gz](run-053.json.gz) |
| 54 | pass | fail | pass | pass | pass | [run-054.json.gz](run-054.json.gz) |
| 55 | pass | fail | pass | pass | pass | [run-055.json.gz](run-055.json.gz) |
| 56 | pass | pass | pass | pass | pass | [run-056.json.gz](run-056.json.gz) |
| 57 | pass | pass | pass | pass | pass | [run-057.json.gz](run-057.json.gz) |
| 58 | pass | fail | pass | pass | pass | [run-058.json.gz](run-058.json.gz) |
| 59 | pass | fail | pass | pass | pass | [run-059.json.gz](run-059.json.gz) |
| 60 | pass | fail | pass | pass | pass | [run-060.json.gz](run-060.json.gz) |
| 61 | pass | fail | pass | pass | pass | [run-061.json.gz](run-061.json.gz) |
| 62 | pass | fail | pass | pass | pass | [run-062.json.gz](run-062.json.gz) |
| 63 | pass | fail | pass | pass | pass | [run-063.json.gz](run-063.json.gz) |
| 64 | pass | fail | pass | pass | pass | [run-064.json.gz](run-064.json.gz) |
| 65 | pass | fail | pass | pass | pass | [run-065.json.gz](run-065.json.gz) |
| 66 | pass | fail | pass | pass | pass | [run-066.json.gz](run-066.json.gz) |
| 67 | pass | fail | pass | pass | pass | [run-067.json.gz](run-067.json.gz) |
| 68 | pass | fail | pass | pass | pass | [run-068.json.gz](run-068.json.gz) |
| 69 | pass | fail | pass | pass | pass | [run-069.json.gz](run-069.json.gz) |
| 70 | pass | fail | pass | pass | pass | [run-070.json.gz](run-070.json.gz) |
| 71 | pass | fail | pass | pass | pass | [run-071.json.gz](run-071.json.gz) |
| 72 | pass | pass | pass | pass | pass | [run-072.json.gz](run-072.json.gz) |
| 73 | pass | fail | pass | pass | pass | [run-073.json.gz](run-073.json.gz) |
| 74 | pass | fail | pass | pass | pass | [run-074.json.gz](run-074.json.gz) |
| 75 | pass | fail | pass | pass | pass | [run-075.json.gz](run-075.json.gz) |
| 76 | pass | fail | pass | pass | pass | [run-076.json.gz](run-076.json.gz) |
| 77 | pass | fail | pass | pass | pass | [run-077.json.gz](run-077.json.gz) |
| 78 | pass | fail | pass | pass | pass | [run-078.json.gz](run-078.json.gz) |
| 79 | pass | fail | pass | pass | pass | [run-079.json.gz](run-079.json.gz) |
| 80 | pass | fail | pass | pass | pass | [run-080.json.gz](run-080.json.gz) |
| 81 | pass | pass | pass | pass | pass | [run-081.json.gz](run-081.json.gz) |
| 82 | pass | fail | pass | pass | pass | [run-082.json.gz](run-082.json.gz) |
| 83 | pass | pass | pass | pass | pass | [run-083.json.gz](run-083.json.gz) |
| 84 | pass | fail | pass | pass | pass | [run-084.json.gz](run-084.json.gz) |
| 85 | pass | fail | pass | pass | pass | [run-085.json.gz](run-085.json.gz) |
| 86 | pass | fail | pass | pass | pass | [run-086.json.gz](run-086.json.gz) |
| 87 | pass | fail | pass | pass | pass | [run-087.json.gz](run-087.json.gz) |
| 88 | pass | fail | pass | pass | pass | [run-088.json.gz](run-088.json.gz) |
| 89 | pass | fail | pass | pass | pass | [run-089.json.gz](run-089.json.gz) |
| 90 | pass | fail | pass | pass | pass | [run-090.json.gz](run-090.json.gz) |
| 91 | pass | fail | pass | pass | pass | [run-091.json.gz](run-091.json.gz) |
| 92 | pass | pass | pass | pass | pass | [run-092.json.gz](run-092.json.gz) |
| 93 | pass | fail | pass | pass | pass | [run-093.json.gz](run-093.json.gz) |
| 94 | pass | pass | pass | pass | pass | [run-094.json.gz](run-094.json.gz) |
| 95 | pass | fail | pass | pass | pass | [run-095.json.gz](run-095.json.gz) |
| 96 | pass | fail | pass | pass | pass | [run-096.json.gz](run-096.json.gz) |
| 97 | pass | fail | pass | pass | pass | [run-097.json.gz](run-097.json.gz) |
| 98 | pass | pass | pass | pass | pass | [run-098.json.gz](run-098.json.gz) |
| 99 | pass | fail | pass | pass | pass | [run-099.json.gz](run-099.json.gz) |
| 100 | pass | fail | pass | pass | pass | [run-100.json.gz](run-100.json.gz) |

## Failed and inconclusive verdicts

- Run 1, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 2, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 4, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 6, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 7, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 6
- Run 7, one_order_per_cart fail: cart c-2 (cart_01M7X19VJ1YND7PXK9T5WZG5ZY) is linked to 2 orders: order_01M7X19X3KGW1NE6106A411YJG, order_01M7X19X3R7WQ8FT7R47CZJMWP; cart c-2: ok complete calls returned 2 different orders (x2-2#53=order_01M7X19X3KGW1NE6106A411YJG, x1-2#57=order_01M7X19X3R7WQ8FT7R47CZJMWP)
- Run 8, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 6
- Run 8, one_order_per_cart fail: cart c-5 (cart_01M7X1A31DGR8VPGCPY0YBTBJ7) is linked to 2 orders: order_01M7X1A3HRTZ7M0FEDJYGBZW3Z, order_01M7X1A3J0TR19VQF3WBA3PKA3; cart c-5: ok complete calls returned 2 different orders (x1-5#58=order_01M7X1A3HRTZ7M0FEDJYGBZW3Z, x2-5#60=order_01M7X1A3J0TR19VQF3WBA3PKA3)
- Run 9, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 10, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 11, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 12, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 13, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 14, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 15, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 16, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 17, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 19, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 6
- Run 19, one_order_per_cart fail: cart c-4 (cart_01M7X1CJ2SFKB0Y2YH7Q7M4GHM) is linked to 2 orders: order_01M7X1CK84G7PJPMJ86HVJ5B28, order_01M7X1CK8N0JNG06KXVT90RCP0; cart c-4: ok complete calls returned 2 different orders (x2-4#53=order_01M7X1CK8N0JNG06KXVT90RCP0, x1-4#56=order_01M7X1CK84G7PJPMJ86HVJ5B28)
- Run 20, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 21, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 22, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 23, reserved_matches_reservations fail: WIDGET reserved_quantity 5 but live reservations sum to 7
- Run 23, one_order_per_cart fail: cart c-2 (cart_01M7X1DDAEBPE6MEDRKKMKMEAQ) is linked to 2 orders: order_01M7X1DEWB8CTMHC25Q757MS41, order_01M7X1DEX8K7AZEZV4ZXKPTNH0; cart c-4 (cart_01M7X1DE0T0B8DEXN0KS4V5XSZ) is linked to 2 orders: order_01M7X1DEVZBEW7XSZPEN8YDW7D, order_01M7X1DEWS7R99W1HPVK4PX720; cart c-2: ok complete calls returned 2 different orders (x2-2#55=order_01M7X1DEX8K7AZEZV4ZXKPTNH0, x1-2#57=order_01M7X1DEWB8CTMHC25Q757MS41); cart c-4: ok complete calls returned 2 different orders (x1-4#51=order_01M7X1DEVZBEW7XSZPEN8YDW7D, x2-4#54=order_01M7X1DEWS7R99W1HPVK4PX720)
- Run 24, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 25, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 26, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 27, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 28, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 30, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 31, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 5
- Run 32, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 33, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 34, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 36, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 5
- Run 37, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 38, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 39, reserved_matches_reservations fail: WIDGET reserved_quantity 1 but live reservations sum to 5
- Run 40, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 42, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 43, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 45, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 46, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 47, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 49, reserved_matches_reservations fail: WIDGET reserved_quantity 2 but live reservations sum to 5
- Run 50, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 51, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 52, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 53, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 54, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 55, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 58, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 59, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 60, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 61, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 62, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 63, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 64, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 65, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 66, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 67, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 68, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 69, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 70, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 71, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 73, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 74, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 75, reserved_matches_reservations fail: WIDGET reserved_quantity 3 but live reservations sum to 5
- Run 76, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 77, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 78, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 79, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 80, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 82, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 84, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 85, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 86, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 87, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 88, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 89, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 90, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 91, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 93, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 95, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 96, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 97, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 99, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
- Run 100, reserved_matches_reservations fail: WIDGET reserved_quantity 4 but live reservations sum to 5
