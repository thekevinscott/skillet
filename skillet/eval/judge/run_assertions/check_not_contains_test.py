"""Tests for check_not_contains."""

from skillet.eval.judge.run_assertions.check_not_contains import check_not_contains


def describe_check_not_contains():
    def it_passes_when_value_absent():
        assert check_not_contains("5", response_lower="the answer is 4") is None

    def it_fails_when_value_present():
        result = check_not_contains("5", response_lower="the answer is 5")
        assert result is not None
        assert "not_contains" in result

    def it_is_case_insensitive():
        result = check_not_contains("hello", response_lower="hello world")
        assert result is not None
