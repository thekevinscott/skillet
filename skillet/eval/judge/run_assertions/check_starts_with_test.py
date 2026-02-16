"""Tests for check_starts_with."""

from skillet.eval.judge.run_assertions.check_starts_with import check_starts_with


def describe_check_starts_with():
    def it_passes_when_response_starts_with_value():
        assert check_starts_with("hello", response_lower="hello world") is None

    def it_fails_when_response_does_not_start_with_value():
        result = check_starts_with("world", response_lower="hello world")
        assert result is not None
        assert "starts_with" in result

    def it_is_case_insensitive():
        assert check_starts_with("Hello", response_lower="hello world") is None
