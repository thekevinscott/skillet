"""Tests for text utilities."""

import pytest

from skillet._internal.text import (
    strip_markdown,
    summarize_failure_for_eval,
    summarize_failure_for_tuning,
    truncate_response,
)


def describe_strip_markdown():
    """Tests for strip_markdown function."""

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("hello world", "hello world"),
            ("```markdown\nhello world", "hello world"),
            ("```\nhello world", "hello world"),
            ("hello world\n```", "hello world"),
            ("```markdown\nhello world\n```", "hello world"),
            ("  ```markdown\nhello\n```  ", "hello"),
        ],
    )
    def it_strips_markdown_fences(input_text, expected):
        assert strip_markdown(input_text) == expected


def describe_truncate_response():
    """Tests for truncate_response function."""

    @pytest.mark.parametrize(
        "input_text,max_length,expected_len",
        [
            ("short text", 500, 10),
            ("a" * 600, 500, 500),
            ("hello world", 5, 5),
        ],
    )
    def it_truncates_to_max_length(input_text, max_length, expected_len):
        result = truncate_response(input_text, max_length=max_length)
        assert len(result) == expected_len

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            (None, ""),
            ("", ""),
        ],
    )
    def it_handles_empty_values(input_text, expected):
        assert truncate_response(input_text) == expected


def describe_summarize_failure_for_eval():
    """Tests for summarize_failure_for_eval function."""

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


def describe_summarize_failure_for_tuning():
    """Tests for summarize_failure_for_tuning function."""

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
