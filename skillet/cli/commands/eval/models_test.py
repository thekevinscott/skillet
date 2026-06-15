"""Tests for the eval command models."""

from skillet.cli.commands.eval.models import Summary


def describe_summary():
    def it_constructs_from_bullets():
        summary = Summary(bullets=["first pattern", "second pattern"])
        assert summary.bullets == ["first pattern", "second pattern"]

    def it_round_trips_through_validation():
        summary = Summary.model_validate({"bullets": ["only"]})
        assert summary.model_dump() == {"bullets": ["only"]}
