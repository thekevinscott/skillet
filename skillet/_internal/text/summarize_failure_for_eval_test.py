"""Tests for text/summarize_failure_for_eval module."""

from skillet._internal.text.summarize_failure_for_eval import summarize_failure_for_eval


def describe_summarize_failure_for_eval():
    def it_extracts_expected_field():
        result = {"expected": "foo", "response": "bar", "judgment": {"reasoning": "x"}}
        summary = summarize_failure_for_eval(result)
        assert summary["expected"] == "foo"

    def it_truncates_response():
        result = {"expected": "", "response": "a" * 600, "judgment": {"reasoning": ""}}
        summary = summarize_failure_for_eval(result)
        assert len(summary["response_preview"]) == 500

    def it_extracts_reasoning():
        result = {"expected": "", "response": "", "judgment": {"reasoning": "failed because X"}}
        summary = summarize_failure_for_eval(result)
        assert summary["judgment"] == "failed because X"

    def it_handles_missing_fields():
        result = {}
        summary = summarize_failure_for_eval(result)
        assert summary["expected"] == ""
        assert summary["response_preview"] == ""
        assert summary["judgment"] == ""
