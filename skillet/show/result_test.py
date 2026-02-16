"""Tests for show result dataclasses."""

from skillet.show.result import ShowEvalResult, ShowResult


def describe_show_eval_result():
    def it_constructs_with_all_fields():
        r = ShowEvalResult(
            source="001.yaml",
            iterations=[{"iteration": 1, "pass": True}],
            pass_rate=100.0,
        )
        assert r.source == "001.yaml"
        assert len(r.iterations) == 1
        assert r.pass_rate == 100.0

    def it_accepts_none_pass_rate():
        r = ShowEvalResult(source="001.yaml", iterations=[], pass_rate=None)
        assert r.pass_rate is None


def describe_show_result():
    def it_constructs_and_serializes():
        result = ShowResult(
            name="test",
            evals=[
                ShowEvalResult(
                    source="001.yaml",
                    iterations=[{"iteration": 1, "pass": True}],
                    pass_rate=100.0,
                )
            ],
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert len(d["evals"]) == 1
        assert d["evals"][0]["source"] == "001.yaml"
        assert d["evals"][0]["pass_rate"] == 100.0
