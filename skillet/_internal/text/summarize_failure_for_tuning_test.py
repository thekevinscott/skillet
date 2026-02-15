"""Tests for text/summarize_failure_for_tuning module."""

from skillet._internal.text.summarize_failure_for_tuning import summarize_failure_for_tuning


def describe_summarize_failure_for_tuning():
    def it_includes_prompt():
        result = {
            "prompt": "question",
            "expected": "",
            "response": "",
            "judgment": {"reasoning": ""},
        }
        summary = summarize_failure_for_tuning(result)
        assert summary["prompt"] == "question"

    def it_truncates_response():
        result = {
            "prompt": "",
            "expected": "",
            "response": "b" * 600,
            "judgment": {"reasoning": ""},
        }
        summary = summarize_failure_for_tuning(result)
        assert len(summary["actual_response"]) == 500

    def it_includes_why_failed():
        result = {"prompt": "", "expected": "", "response": "", "judgment": {"reasoning": "reason"}}
        summary = summarize_failure_for_tuning(result)
        assert summary["why_failed"] == "reason"
