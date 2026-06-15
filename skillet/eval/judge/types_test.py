"""Tests for the judge types."""

from skillet.eval.judge.types import Judgment


def describe_judgment():
    def it_validates_from_the_pass_alias():
        judgment = Judgment.model_validate({"pass": True, "reasoning": "looks good"})
        assert judgment.passed is True
        assert judgment.reasoning == "looks good"

    def it_populates_by_field_name():
        judgment = Judgment.model_validate({"passed": False})
        assert judgment.passed is False

    def it_defaults_reasoning_to_empty_string():
        judgment = Judgment.model_validate({"pass": True})
        assert judgment.reasoning == ""

    def it_serializes_back_to_the_pass_alias():
        judgment = Judgment.model_validate({"pass": True, "reasoning": "ok"})
        assert judgment.model_dump(by_alias=True) == {"pass": True, "reasoning": "ok"}
