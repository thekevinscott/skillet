"""Tests for results_to_eval_results function."""

import pytest

from skillet.tune.result import EvalResult
from skillet.tune.results_to_eval_results import results_to_eval_results


@pytest.mark.parametrize(
    "results,expected_len,expected_sources,expected_passed",
    [
        # Empty list
        ([], 0, [], []),
        # Single passing result
        (
            [
                {
                    "eval_source": "test.yaml",
                    "pass": True,
                    "judgment": {"reasoning": "looks good"},
                    "response": "the response",
                    "tool_calls": [{"name": "read"}],
                }
            ],
            1,
            ["test.yaml"],
            [True],
        ),
        # Multiple results
        (
            [
                {
                    "eval_source": "a.yaml",
                    "pass": True,
                    "judgment": {"reasoning": "passed"},
                    "response": "resp1",
                    "tool_calls": [],
                },
                {
                    "eval_source": "b.yaml",
                    "pass": False,
                    "judgment": {"reasoning": "failed"},
                    "response": "resp2",
                    "tool_calls": None,
                },
            ],
            2,
            ["a.yaml", "b.yaml"],
            [True, False],
        ),
    ],
    ids=["empty_list", "single_result", "multiple_results"],
)
def test_results_to_eval_results(results, expected_len, expected_sources, expected_passed):
    """Test conversion of raw results to EvalResult objects."""
    converted = results_to_eval_results(results)

    assert len(converted) == expected_len
    for i, result in enumerate(converted):
        assert isinstance(result, EvalResult)
        assert result.source == expected_sources[i]
        assert result.passed == expected_passed[i]


def test_it_extracts_all_fields():
    """Test that all fields are properly extracted."""
    results = [
        {
            "eval_source": "test.yaml",
            "pass": True,
            "judgment": {"reasoning": "looks good"},
            "response": "the response",
            "tool_calls": [{"name": "read"}],
        }
    ]
    converted = results_to_eval_results(results)

    assert converted[0].source == "test.yaml"
    assert converted[0].passed is True
    assert converted[0].reasoning == "looks good"
    assert converted[0].response == "the response"
    assert converted[0].tool_calls == [{"name": "read"}]


def test_it_handles_missing_optional_fields():
    """Test handling of missing optional fields."""
    results = [
        {
            "eval_source": "test.yaml",
            "pass": False,
            "judgment": {},  # missing reasoning
        }
    ]
    converted = results_to_eval_results(results)

    assert len(converted) == 1
    assert converted[0].reasoning == ""
    assert converted[0].response is None
    assert converted[0].tool_calls is None
