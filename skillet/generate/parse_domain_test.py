"""Tests for domain string parsing."""

import pytest

from skillet.generate.parse_domain import parse_domain
from skillet.generate.types import EvalDomain


def describe_parse_domain():
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("triggering", EvalDomain.TRIGGERING),
            ("functional", EvalDomain.FUNCTIONAL),
            ("performance", EvalDomain.PERFORMANCE),
            ("TRIGGERING", EvalDomain.TRIGGERING),
            (" functional ", EvalDomain.FUNCTIONAL),
        ],
    )
    def it_parses_valid_domain_strings(value, expected):
        assert parse_domain(value) == expected

    @pytest.mark.parametrize("value", ["invalid", "trigger", ""])
    def it_returns_none_for_invalid_strings(value):
        assert parse_domain(value) is None
