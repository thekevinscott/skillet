"""Tests for tune/run module."""

from skillet.tune.result import EvalResult
from skillet.tune.run import _results_to_eval_results


def describe_results_to_eval_results():
    """Tests for _results_to_eval_results function."""

    def it_converts_empty_list():
        result = _results_to_eval_results([])
        assert result == []

    def it_converts_single_result():
        results = [
            {
                "gap_source": "test.yaml",
                "pass": True,
                "judgment": {"reasoning": "looks good"},
                "response": "the response",
                "tool_calls": [{"name": "read"}],
            }
        ]
        converted = _results_to_eval_results(results)

        assert len(converted) == 1
        assert isinstance(converted[0], EvalResult)
        assert converted[0].source == "test.yaml"
        assert converted[0].passed is True
        assert converted[0].reasoning == "looks good"
        assert converted[0].response == "the response"
        assert converted[0].tool_calls == [{"name": "read"}]

    def it_converts_multiple_results():
        results = [
            {
                "gap_source": "a.yaml",
                "pass": True,
                "judgment": {"reasoning": "passed"},
                "response": "resp1",
                "tool_calls": [],
            },
            {
                "gap_source": "b.yaml",
                "pass": False,
                "judgment": {"reasoning": "failed"},
                "response": "resp2",
                "tool_calls": None,
            },
        ]
        converted = _results_to_eval_results(results)

        assert len(converted) == 2
        assert converted[0].source == "a.yaml"
        assert converted[0].passed is True
        assert converted[1].source == "b.yaml"
        assert converted[1].passed is False

    def it_handles_missing_optional_fields():
        results = [
            {
                "gap_source": "test.yaml",
                "pass": False,
                "judgment": {},  # missing reasoning
            }
        ]
        converted = _results_to_eval_results(results)

        assert len(converted) == 1
        assert converted[0].reasoning == ""
        assert converted[0].response is None
        assert converted[0].tool_calls is None
