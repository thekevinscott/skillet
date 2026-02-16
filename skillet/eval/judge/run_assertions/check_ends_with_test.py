"""Tests for check_ends_with."""

from skillet.eval.judge.run_assertions.check_ends_with import check_ends_with


def describe_check_ends_with():
    def it_passes_when_response_ends_with_value():
        assert check_ends_with("world", response_lower="hello world") is None

    def it_fails_when_response_does_not_end_with_value():
        result = check_ends_with("hello", response_lower="hello world")
        assert result is not None
        assert "ends_with" in result

    def it_strips_trailing_whitespace():
        assert check_ends_with("world", response_lower="hello world\n") is None

    def it_is_case_insensitive():
        assert check_ends_with("World", response_lower="hello world") is None
