"""Calculate pass@k metric from eval sample results."""

from math import comb


def pass_at_k(n: int, c: int, k: int) -> float | None:
    """Probability of at least one success when drawing k from n samples with c successes."""
    if n == 0 or k > n:
        return None
    if c == 0:
        return 0.0
    return 1.0 - comb(n - c, k) / comb(n, k)
