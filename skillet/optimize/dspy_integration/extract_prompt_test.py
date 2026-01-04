"""Tests for prompt extraction utilities."""

import pytest

from skillet.optimize.dspy_integration.extract_prompt import extract_prompt


@pytest.mark.parametrize(
    "prompt,messages,expected",
    [
        # Simple prompt passthrough
        ("Hello world", None, "Hello world"),
        # Empty inputs
        (None, None, ""),
        # Extract last user message
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
            ],
            "Second question",
        ),
        # Concatenate when no user message
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello"},
            ],
            "system: System prompt\nassistant: Hello",
        ),
        # Messages take precedence over prompt
        (
            "From prompt",
            [{"role": "user", "content": "From messages"}],
            "From messages",
        ),
        # Empty messages list falls back to prompt
        ("Fallback", [], "Fallback"),
        # Missing content field
        (None, [{"role": "user"}], ""),
    ],
    ids=[
        "simple_prompt",
        "empty_inputs",
        "last_user_message",
        "concatenate_no_user",
        "messages_precedence",
        "empty_messages_fallback",
        "missing_content",
    ],
)
def test_extract_prompt(prompt, messages, expected):
    """Test extract_prompt with various input combinations."""
    assert extract_prompt(prompt, messages) == expected
