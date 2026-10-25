ISSUE_17032 = "https://github.com/medusajs/medusa/issues/17032"
ISSUE_16502 = "https://github.com/medusajs/medusa/issues/16502"
ISSUE_16825 = "https://github.com/medusajs/medusa/issues/16825"

MANUAL_CHECK = frozenset({ISSUE_16825})


def covering_issues(shape: dict, rule: str) -> tuple[str, ...]:
    issues = []
    if shape["servers"] == 2 and rule in ("no_oversell", "reserved_matches_reservations"):
        issues.append(ISSUE_17032)
    if rule == "no_oversell" and shape["item_on_several_lines"]:
        issues.append(ISSUE_16502)
        if shape["carts"] > 1 and ISSUE_17032 not in issues:
            issues.append(ISSUE_17032)
    if rule == "no_orphaned_orders" and shape["carts"] > 1 and shape["release"] == "together":
        issues.append(ISSUE_16825)
    return tuple(issues)
