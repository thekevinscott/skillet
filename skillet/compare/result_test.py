"""Tests for compare result dataclasses."""

from pathlib import Path

from skillet.compare.result import CompareEvalResult, CompareResult


def describe_compare_eval_result():
    def it_constructs_with_all_fields():
        r = CompareEvalResult(source="001.yaml", baseline=80.0, skill=90.0)
        assert r.source == "001.yaml"
        assert r.baseline == 80.0
        assert r.skill == 90.0

    def it_accepts_none_values():
        r = CompareEvalResult(source="001.yaml", baseline=None, skill=None)
        assert r.baseline is None
        assert r.skill is None


def describe_compare_result():
    def it_constructs_and_serializes():
        result = CompareResult(
            name="test",
            skill_path=Path("/tmp/skill"),
            results=[CompareEvalResult(source="001.yaml", baseline=50.0, skill=75.0)],
            overall_baseline=50.0,
            overall_skill=75.0,
            baseline_total=2,
            baseline_pass=1,
            skill_total=2,
            skill_pass=1,
            missing_baseline=[],
            missing_skill=[],
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert isinstance(d["skill_path"], Path)
        assert len(d["results"]) == 1
        assert d["results"][0]["source"] == "001.yaml"
