"""Tests for extract_examples."""

import pytest

from .extract_examples import extract_examples


def describe_extract_examples():
    """Tests for extract_examples function."""

    def it_extracts_single_code_block():
        body = '\n## Example\n\n```python\nprint("hello")\n```\n'
        examples = extract_examples(body)

        assert examples == ['print("hello")\n']

    def it_extracts_multiple_code_blocks():
        body = "\n```python\ncode1()\n```\n\nSome text\n\n```bash\ncode2\n```\n"
        examples = extract_examples(body)

        assert len(examples) == 2
        assert "code1()" in examples[0]
        assert "code2" in examples[1]

    def it_handles_code_block_without_language():
        body = "\n```\nplain code\n```\n"
        examples = extract_examples(body)

        assert examples == ["plain code\n"]

    def it_returns_empty_for_no_code_blocks():
        body = "Just plain text without any code blocks."
        examples = extract_examples(body)

        assert examples == []

    def it_handles_multiline_code_blocks():
        body = "\n```python\ndef foo():\n    bar()\n    baz()\n```\n"
        examples = extract_examples(body)

        assert len(examples) == 1
        assert "def foo():" in examples[0]
        assert "bar()" in examples[0]
        assert "baz()" in examples[0]

    def it_preserves_whitespace_in_code():
        body = "\n```\n  indented\n    more indented\n```\n"
        examples = extract_examples(body)

        assert "  indented" in examples[0]
        assert "    more indented" in examples[0]


@pytest.mark.parametrize(
    ("body", "expected_count"),
    [
        ("no code", 0),
        ("```\ncode\n```", 1),
        ("```\na\n```\n```\nb\n```", 2),
        ("```python\ncode\n```", 1),
    ],
    ids=["no-code", "single", "multiple", "with-lang"],
)
def test_extract_examples_parametrized(body: str, expected_count: int):
    assert len(extract_examples(body)) == expected_count
