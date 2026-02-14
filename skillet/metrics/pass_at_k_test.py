"""Tests for pass@k metric calculation."""

import pytest

from skillet.metrics.pass_at_k import pass_at_k


def describe_pass_at_k():
    """Probability of at least one success in k draws."""

    def it_returns_1_when_all_pass():
        assert pass_at_k(n=5, c=5, k=3) == 1.0

    def it_returns_0_when_none_pass():
        assert pass_at_k(n=5, c=0, k=3) == 0.0

    def it_computes_correctly_for_partial():
        # n=10, c=3, k=5: 1 - C(7,5)/C(10,5)
        # C(7,5)=21, C(10,5)=252 → 1 - 21/252 = 1 - 1/12 ≈ 0.9167
        result = pass_at_k(n=10, c=3, k=5)
        assert result == pytest.approx(1 - 21 / 252)

    def it_returns_1_when_k_equals_1_and_any_pass():
        # pass@1 with at least one success: 1 - C(n-c, 1)/C(n, 1) = c/n
        result = pass_at_k(n=10, c=3, k=1)
        assert result == pytest.approx(0.3)

    def it_returns_none_when_k_exceeds_n():
        assert pass_at_k(n=3, c=2, k=5) is None

    def it_returns_none_when_n_is_zero():
        assert pass_at_k(n=0, c=0, k=1) is None
