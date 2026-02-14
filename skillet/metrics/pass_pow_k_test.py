"""Tests for pass^k metric calculation."""

import pytest

from skillet.metrics.pass_pow_k import pass_pow_k


def describe_pass_pow_k():
    """Probability all k draws succeed."""

    def it_returns_1_when_all_pass():
        assert pass_pow_k(n=5, c=5, k=3) == 1.0

    def it_returns_0_when_none_pass():
        assert pass_pow_k(n=5, c=0, k=3) == 0.0

    def it_computes_correctly_for_partial():
        # n=10, c=6, k=3: C(6,3)/C(10,3)
        # C(6,3)=20, C(10,3)=120 → 20/120 = 1/6 ≈ 0.1667
        result = pass_pow_k(n=10, c=6, k=3)
        assert result == pytest.approx(20 / 120)

    def it_returns_0_when_c_less_than_k():
        assert pass_pow_k(n=10, c=2, k=3) == 0.0

    def it_returns_none_when_k_exceeds_n():
        assert pass_pow_k(n=3, c=2, k=5) is None

    def it_returns_none_when_n_is_zero():
        assert pass_pow_k(n=0, c=0, k=1) is None
