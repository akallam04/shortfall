import math
from fractions import Fraction


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    rows = (a + b, c + d)
    col = a + c
    n = a + b + c + d
    low = max(0, col - rows[1])
    high = min(rows[0], col)
    total = math.comb(n, col)

    def prob(x: int) -> Fraction:
        return Fraction(math.comb(rows[0], x) * math.comb(rows[1], col - x), total)

    seen = prob(a)
    return float(sum((prob(x) for x in range(low, high + 1) if prob(x) <= seen), Fraction(0)))


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def mann_whitney(x: list[float], y: list[float]) -> float:
    n1, n2 = len(x), len(y)
    n = n1 + n2
    r = ranks(list(x) + list(y))
    u1 = sum(r[:n1]) - n1 * (n1 + 1) / 2
    u = max(u1, n1 * n2 - u1)
    counts: dict[float, int] = {}
    for v in list(x) + list(y):
        counts[v] = counts.get(v, 0) + 1
    ties = sum(t**3 - t for t in counts.values())
    sd = math.sqrt(n1 * n2 / 12 * ((n + 1) - ties / (n * (n - 1))))
    if sd == 0:
        return 1.0
    z = (u - n1 * n2 / 2 - 0.5) / sd
    return min(1.0, math.erfc(z / math.sqrt(2)))


def holm(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    out = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        out[i] = running
    return out
