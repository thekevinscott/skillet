"""Tests for pass rate threshold helpers."""

from skillet.cli.display.thresholds import (
    PASS_RATE_GREEN,
    PASS_RATE_YELLOW,
    get_rate_color,
)


def describe_constants():
    """Tests for threshold constants."""

    def it_has_green_threshold_at_80():
        assert PASS_RATE_GREEN == 80

    def it_has_yellow_threshold_at_50():
        assert PASS_RATE_YELLOW == 50


def describe_get_rate_color():
    """Tests for get_rate_color function."""

    def it_returns_green_at_100():
        assert get_rate_color(100) == "green"

    def it_returns_green_at_80():
        assert get_rate_color(80) == "green"

    def it_returns_yellow_at_79():
        assert get_rate_color(79) == "yellow"

    def it_returns_yellow_at_50():
        assert get_rate_color(50) == "yellow"

    def it_returns_red_at_49():
        assert get_rate_color(49) == "red"

    def it_returns_red_at_0():
        assert get_rate_color(0) == "red"

    def it_handles_float_values():
        assert get_rate_color(80.0) == "green"
        assert get_rate_color(79.9) == "yellow"
        assert get_rate_color(50.0) == "yellow"
        assert get_rate_color(49.9) == "red"
