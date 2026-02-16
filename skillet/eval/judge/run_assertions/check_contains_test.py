"""Tests for check_contains."""

from skillet.eval.judge.run_assertions.check_contains import check_contains


def describe_check_contains():
    def it_passes_when_value_present():
        assert check_contains("4", response_lower="the answer is 4") is None

    def it_fails_when_value_absent():
        result = check_contains("42", response_lower="the answer is 4")
        assert result is not None
        assert "contains" in result

    def it_is_case_insensitive():
        assert check_contains("hello", response_lower="hello world") is None

    def it_matches_partial_strings():
        assert check_contains("swer", response_lower="the answer is 4") is None
