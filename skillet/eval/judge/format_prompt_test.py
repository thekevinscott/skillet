"""Tests for judge/format_prompt module."""

from skillet.eval.judge.format_prompt import format_prompt


def describe_format_prompt():
    def it_returns_string_prompt_unchanged():
        result = format_prompt("simple prompt")
        assert result == "simple prompt"

    def it_formats_multi_turn_prompts():
        prompts = ["first message", "second message", "third message"]
        result = format_prompt(prompts)
        assert "Turn 1: first message" in result
        assert "Turn 2: second message" in result
        assert "Turn 3: third message" in result

    def it_handles_single_item_list():
        result = format_prompt(["only one"])
        assert result == "Turn 1: only one"
