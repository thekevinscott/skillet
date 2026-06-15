"""Tests for the live display types."""

from skillet.cli.display.live.types import EvalGroup


def describe_eval_group():
    def it_holds_a_source_and_iterations():
        group: EvalGroup = {"source": "001.yaml", "iterations": [{"pass": True}]}
        assert group["source"] == "001.yaml"
        assert group["iterations"][0]["pass"] is True

    def it_is_a_plain_dict_at_runtime():
        group = EvalGroup(source="002.yaml", iterations=[])
        assert group == {"source": "002.yaml", "iterations": []}
