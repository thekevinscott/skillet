"""Calculate pass^k metric from eval sample results."""

from math import comb


def pass_pow_k(n: int, c: int, k: int) -> float | None:
    """Probability all k draws succeed when drawing from n samples with c successes."""
    if n == 0 or k > n:
        return None
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)
