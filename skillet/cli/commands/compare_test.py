"""Tests for cli/commands/compare module."""

import pytest

from skillet.cli.commands.compare import format_delta


def describe_format_delta():
    """Tests for format_delta function."""

    @pytest.mark.parametrize(
        "baseline,skill,expected",
        [
            (None, 80.0, "-"),
            (80.0, None, "-"),
            (None, None, "-"),
        ],
    )
    def it_returns_dash_for_missing_values(baseline, skill, expected):
        assert format_delta(baseline, skill) == expected

    def it_returns_positive_delta_in_green():
        result = format_delta(50.0, 80.0)
        assert "[green]" in result
        assert "+30%" in result

    def it_returns_negative_delta_in_red():
        result = format_delta(80.0, 50.0)
        assert "[red]" in result
        assert "-30%" in result

    def it_returns_zero_for_no_change():
        result = format_delta(75.0, 75.0)
        assert result == "0%"
