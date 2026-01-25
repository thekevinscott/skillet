"""Tests for format utilities."""

import pytest

from .format_utils import EXPECTED_TRUNCATE, PROMPT_TRUNCATE, format_prompt, truncate


def describe_truncate():
    """Tests for truncate function."""

    def it_returns_original_if_short():
        assert truncate("short", 100) == "short"

    def it_truncates_long_text():
        result = truncate("a" * 50, 10)
        assert result == "aaaaaaaaaa..."
        assert len(result) == 13

    def it_handles_exact_length():
        assert truncate("exact", 5) == "exact"

    def it_handles_empty_string():
        assert truncate("", 10) == ""


def describe_format_prompt():
    """Tests for format_prompt function."""

    def it_returns_string_unchanged():
        assert format_prompt("single prompt") == "single prompt"

    def it_joins_list_with_pipe():
        result = format_prompt(["first", "second", "third"])
        assert result == "first | second | third"

    def it_handles_single_item_list():
        assert format_prompt(["only one"]) == "only one"

    def it_handles_empty_list():
        assert format_prompt([]) == ""


@pytest.mark.parametrize(
    ("text", "max_len", "expected"),
    [
        ("short", 100, "short"),
        ("exact", 5, "exact"),
        ("toolong", 5, "toolo..."),
        ("", 10, ""),
    ],
    ids=["short", "exact", "long", "empty"],
)
def test_truncate_parametrized(text: str, max_len: int, expected: str):
    assert truncate(text, max_len) == expected


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("single", "single"),
        (["a", "b"], "a | b"),
        ([], ""),
    ],
    ids=["string", "list", "empty-list"],
)
def test_format_prompt_parametrized(prompt: str | list[str], expected: str):
    assert format_prompt(prompt) == expected


def describe_constants():
    """Tests for constant values."""

    def it_has_reasonable_prompt_truncate():
        assert PROMPT_TRUNCATE == 100

    def it_has_reasonable_expected_truncate():
        assert EXPECTED_TRUNCATE == 80
