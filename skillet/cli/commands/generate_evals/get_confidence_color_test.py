"""Tests for get_confidence_color."""

import pytest

from .get_confidence_color import (
    HIGH_CONFIDENCE,
    MEDIUM_CONFIDENCE,
    get_confidence_color,
)


def describe_get_confidence_color():
    """Tests for get_confidence_color function."""

    def it_returns_green_for_high_confidence():
        assert get_confidence_color(0.9) == "green"
        assert get_confidence_color(0.8) == "green"
        assert get_confidence_color(1.0) == "green"

    def it_returns_yellow_for_medium_confidence():
        assert get_confidence_color(0.7) == "yellow"
        assert get_confidence_color(0.6) == "yellow"
        assert get_confidence_color(0.79) == "yellow"

    def it_returns_red_for_low_confidence():
        assert get_confidence_color(0.5) == "red"
        assert get_confidence_color(0.0) == "red"
        assert get_confidence_color(0.59) == "red"


@pytest.mark.parametrize(
    ("confidence", "expected_color"),
    [
        (1.0, "green"),
        (HIGH_CONFIDENCE, "green"),
        (0.79, "yellow"),
        (MEDIUM_CONFIDENCE, "yellow"),
        (0.59, "red"),
        (0.0, "red"),
    ],
    ids=["max", "high-threshold", "below-high", "medium-threshold", "below-medium", "min"],
)
def test_confidence_color_thresholds(confidence: float, expected_color: str):
    assert get_confidence_color(confidence) == expected_color
