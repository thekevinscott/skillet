"""Tests for pass rate threshold helpers."""

import pytest

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

    @pytest.mark.parametrize(
        ("pass_rate", "expected_color"),
        [
            # Green: >= 80
            (100, "green"),
            (80, "green"),
            (80.0, "green"),
            # Yellow: >= 50 and < 80
            (79, "yellow"),
            (79.9, "yellow"),
            (50, "yellow"),
            (50.0, "yellow"),
            # Red: < 50
            (49, "red"),
            (49.9, "red"),
            (0, "red"),
        ],
    )
    def it_returns_correct_color(pass_rate: float, expected_color: str):
        assert get_rate_color(pass_rate) == expected_color
