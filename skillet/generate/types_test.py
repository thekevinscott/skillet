"""Tests for generate module type definitions."""

import pytest

from skillet.generate.types import CandidateEval, EvalDomain


def describe_EvalDomain():
    def it_has_three_domains():
        assert len(EvalDomain) == 3

    @pytest.mark.parametrize(
        "member,value",
        [
            (EvalDomain.TRIGGERING, "triggering"),
            (EvalDomain.FUNCTIONAL, "functional"),
            (EvalDomain.PERFORMANCE, "performance"),
        ],
    )
    def it_has_expected_values(member, value):
        assert member.value == value

    @pytest.mark.parametrize("value", ["triggering", "functional", "performance"])
    def it_round_trips_from_string(value):
        assert EvalDomain(value).value == value


def describe_CandidateEval():
    def it_accepts_domain_field():
        eval_ = CandidateEval(
            prompt="test prompt",
            expected="expected behavior",
            name="test-eval",
            category="positive",
            domain=EvalDomain.TRIGGERING,
            source="goal:1",
            confidence=0.9,
            rationale="tests triggering",
        )
        assert eval_.domain == EvalDomain.TRIGGERING

    def it_defaults_domain_to_none():
        eval_ = CandidateEval(
            prompt="test prompt",
            expected="expected behavior",
            name="test-eval",
            category="positive",
            source="goal:1",
            confidence=0.9,
            rationale="tests something",
        )
        assert eval_.domain is None
