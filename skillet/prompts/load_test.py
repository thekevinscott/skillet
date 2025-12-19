"""Tests for prompt loading utilities."""

import tempfile
from pathlib import Path

import pytest

from .load import load_prompt

# Path to judge.txt for testing with a real prompt file
JUDGE_TXT = Path(__file__).parent.parent / "eval" / "judge.txt"


def describe_load_prompt():
    """Tests for load_prompt function."""

    def it_loads_prompt_file():
        result = load_prompt(
            JUDGE_TXT, prompt="test", response="resp", tools="none", expected="exp"
        )
        assert "test" in result
        assert "resp" in result
        assert "exp" in result

    def it_raises_on_missing_variable():
        with pytest.raises(KeyError):
            load_prompt(JUDGE_TXT, prompt="test")  # missing response, tools, expected

    def it_raises_on_missing_file():
        with pytest.raises(FileNotFoundError):
            load_prompt("/nonexistent/path.txt", foo="bar")

    def it_handles_multiline_values():
        multiline = "line1\nline2\nline3"
        result = load_prompt(JUDGE_TXT, prompt=multiline, response="r", tools="t", expected="e")
        assert "line1\nline2\nline3" in result

    def it_substitutes_variables():
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "test.txt"
            txt_path.write_text("Hello ${name}!")

            result = load_prompt(txt_path, name="World")
            assert result == "Hello World!"

    def it_accepts_path_object():
        result = load_prompt(JUDGE_TXT, prompt="p", response="r", tools="t", expected="e")
        assert "p" in result
