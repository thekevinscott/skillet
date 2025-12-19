"""Tests for text utilities."""

from skillet._internal.text import (
    strip_markdown,
    summarize_failure_for_eval,
    summarize_failure_for_tuning,
    truncate_response,
)


def describe_strip_markdown():
    """Tests for strip_markdown function."""

    def it_returns_plain_text_unchanged():
        assert strip_markdown("hello world") == "hello world"

    def it_strips_markdown_fence_prefix():
        assert strip_markdown("```markdown\nhello world") == "hello world"

    def it_strips_plain_code_fence_prefix():
        assert strip_markdown("```\nhello world") == "hello world"

    def it_strips_code_fence_suffix():
        assert strip_markdown("hello world\n```") == "hello world"

    def it_strips_both_fences():
        assert strip_markdown("```markdown\nhello world\n```") == "hello world"

    def it_handles_whitespace():
        assert strip_markdown("  ```markdown\nhello\n```  ") == "hello"


def describe_truncate_response():
    """Tests for truncate_response function."""

    def it_returns_short_text_unchanged():
        assert truncate_response("short text") == "short text"

    def it_truncates_long_text():
        long_text = "a" * 600
        result = truncate_response(long_text)
        assert len(result) == 500

    def it_uses_custom_max_length():
        text = "hello world"
        assert truncate_response(text, max_length=5) == "hello"

    def it_returns_empty_string_for_none():
        assert truncate_response(None) == ""

    def it_returns_empty_string_for_empty():
        assert truncate_response("") == ""


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
