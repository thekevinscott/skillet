"""Tests for compare/calculate_pass_rate module."""

from skillet.compare.calculate_pass_rate import calculate_pass_rate


def describe_calculate_pass_rate():
    """Tests for calculate_pass_rate function."""

    def it_returns_none_for_empty_list():
        result = calculate_pass_rate([])
        assert result is None

    def it_calculates_100_percent_for_all_pass():
        iterations = [{"pass": True}, {"pass": True}, {"pass": True}]
        result = calculate_pass_rate(iterations)
        assert result == 100.0

    def it_calculates_0_percent_for_all_fail():
        iterations = [{"pass": False}, {"pass": False}]
        result = calculate_pass_rate(iterations)
        assert result == 0.0

    def it_calculates_partial_pass_rate():
        iterations = [{"pass": True}, {"pass": False}, {"pass": True}, {"pass": False}]
        result = calculate_pass_rate(iterations)
        assert result == 50.0

    def it_handles_missing_pass_key():
        iterations = [{"other": "data"}, {"pass": True}]
        result = calculate_pass_rate(iterations)
        assert result == 50.0
