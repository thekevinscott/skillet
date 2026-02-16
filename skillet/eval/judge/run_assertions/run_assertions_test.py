"""Tests for run_assertions module."""

import pytest

from skillet.eval.judge.run_assertions import run_assertions


def describe_run_assertions():
    def it_passes_contains_assertion():
        result = run_assertions("The answer is 4", [{"type": "contains", "value": "4"}])
        assert result["pass"] is True

    def it_fails_contains_assertion():
        result = run_assertions("The answer is 4", [{"type": "contains", "value": "42"}])
        assert result["pass"] is False
        assert "contains" in result["reasoning"]

    def it_is_case_insensitive_for_contains():
        result = run_assertions("Hello World", [{"type": "contains", "value": "hello"}])
        assert result["pass"] is True

    def it_passes_not_contains_assertion():
        result = run_assertions("The answer is 4", [{"type": "not_contains", "value": "5"}])
        assert result["pass"] is True

    def it_fails_not_contains_assertion():
        result = run_assertions("The answer is 5", [{"type": "not_contains", "value": "5"}])
        assert result["pass"] is False

    def it_passes_regex_assertion():
        result = run_assertions("The answer is 42", [{"type": "regex", "value": r"\d+"}])
        assert result["pass"] is True

    def it_fails_regex_assertion():
        result = run_assertions("No numbers here", [{"type": "regex", "value": r"^\d+$"}])
        assert result["pass"] is False

    def it_handles_invalid_regex():
        result = run_assertions("test", [{"type": "regex", "value": "[invalid"}])
        assert result["pass"] is False
        assert "invalid pattern" in result["reasoning"]

    def it_supports_case_insensitive_regex_via_flag():
        result = run_assertions("HELLO world", [{"type": "regex", "value": "(?i)hello"}])
        assert result["pass"] is True

    def it_passes_starts_with_assertion():
        result = run_assertions("Hello world", [{"type": "starts_with", "value": "Hello"}])
        assert result["pass"] is True

    def it_is_case_insensitive_for_starts_with():
        result = run_assertions("Hello world", [{"type": "starts_with", "value": "hello"}])
        assert result["pass"] is True

    def it_fails_starts_with_assertion():
        result = run_assertions("Hello world", [{"type": "starts_with", "value": "world"}])
        assert result["pass"] is False

    def it_passes_ends_with_assertion():
        result = run_assertions("Hello world", [{"type": "ends_with", "value": "world"}])
        assert result["pass"] is True

    def it_is_case_insensitive_for_ends_with():
        result = run_assertions("Hello World", [{"type": "ends_with", "value": "world"}])
        assert result["pass"] is True

    def it_strips_trailing_whitespace_for_ends_with():
        result = run_assertions("Hello world\n", [{"type": "ends_with", "value": "world"}])
        assert result["pass"] is True

    def it_passes_tool_called_assertion():
        tool_calls = [{"name": "Read", "input": {}}]
        result = run_assertions("text", [{"type": "tool_called", "value": "Read"}], tool_calls)
        assert result["pass"] is True

    def it_fails_tool_called_when_tool_not_present():
        tool_calls = [{"name": "Write", "input": {}}]
        result = run_assertions("text", [{"type": "tool_called", "value": "Read"}], tool_calls)
        assert result["pass"] is False

    def it_fails_tool_called_when_tool_calls_is_none():
        result = run_assertions("text", [{"type": "tool_called", "value": "Read"}], None)
        assert result["pass"] is False

    def it_passes_tool_not_called_assertion():
        tool_calls = [{"name": "Write", "input": {}}]
        result = run_assertions("text", [{"type": "tool_not_called", "value": "Read"}], tool_calls)
        assert result["pass"] is True

    def it_fails_tool_not_called_when_tool_present():
        tool_calls = [{"name": "Read", "input": {}}]
        result = run_assertions("text", [{"type": "tool_not_called", "value": "Read"}], tool_calls)
        assert result["pass"] is False

    def it_passes_tool_not_called_when_tool_calls_is_none():
        result = run_assertions("text", [{"type": "tool_not_called", "value": "Read"}], None)
        assert result["pass"] is True

    def it_uses_and_semantics():
        result = run_assertions(
            "The answer is 4",
            [
                {"type": "contains", "value": "4"},
                {"type": "contains", "value": "99"},
            ],
        )
        assert result["pass"] is False

    def it_passes_empty_assertions_list():
        result = run_assertions("anything", [])
        assert result["pass"] is True
        assert result["reasoning"] == "All assertions passed"

    @pytest.mark.parametrize(
        "response,assertions,expected_pass",
        [
            ("The answer is 4", [{"type": "contains", "value": "4"}], True),
            ("No match", [{"type": "contains", "value": "4"}], False),
            ("UPPERCASE", [{"type": "contains", "value": "uppercase"}], True),
        ],
    )
    def it_handles_parametrized_cases(response, assertions, expected_pass):
        result = run_assertions(response, assertions)
        assert result["pass"] is expected_pass
