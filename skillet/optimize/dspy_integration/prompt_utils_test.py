"""Tests for prompt extraction utilities."""

from skillet.optimize.dspy_integration.prompt_utils import extract_prompt


def describe_extract_prompt():
    def it_returns_prompt_when_provided():
        result = extract_prompt("Hello world", None)
        assert result == "Hello world"

    def it_returns_empty_string_when_no_input():
        result = extract_prompt(None, None)
        assert result == ""

    def it_extracts_last_user_message():
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]
        result = extract_prompt(None, messages)
        assert result == "Second question"

    def it_concatenates_messages_when_no_user_message():
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "assistant", "content": "Hello"},
        ]
        result = extract_prompt(None, messages)
        assert result == "system: System prompt\nassistant: Hello"

    def it_prefers_messages_over_prompt():
        messages = [{"role": "user", "content": "From messages"}]
        result = extract_prompt("From prompt", messages)
        assert result == "From messages"

    def it_handles_empty_messages_list():
        result = extract_prompt("Fallback", [])
        assert result == "Fallback"

    def it_handles_missing_content():
        messages = [{"role": "user"}]
        result = extract_prompt(None, messages)
        assert result == ""
