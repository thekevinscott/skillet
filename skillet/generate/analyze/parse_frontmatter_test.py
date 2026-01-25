"""Tests for parse_frontmatter."""

import pytest

from .parse_frontmatter import parse_frontmatter


def describe_parse_frontmatter():
    """Tests for parse_frontmatter function."""

    def it_returns_empty_frontmatter_for_no_frontmatter():
        content = "# Just a heading\n\nSome body content."
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def it_parses_valid_yaml_frontmatter():
        content = (
            "---\n"
            "name: test-skill\n"
            "description: A test skill\n"
            "---\n"
            "# Body Content\n"
            "\n"
            "Some text here.\n"
        )
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {"name": "test-skill", "description": "A test skill"}
        assert body.startswith("# Body Content")

    def it_handles_incomplete_frontmatter():
        content = "---\nname: test\nNo closing delimiter"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def it_handles_invalid_yaml():
        content = "---\ninvalid: yaml: content: :::\n---\n# Body\n"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body.startswith("# Body")

    def it_handles_empty_frontmatter():
        content = "---\n---\n# Body\n"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body.startswith("# Body")

    def it_handles_frontmatter_with_lists():
        content = "---\ntags:\n  - python\n  - testing\n---\nBody content\n"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {"tags": ["python", "testing"]}
        assert body == "Body content\n"

    def it_handles_content_with_dashes_in_body():
        content = "---\nname: skill\n---\n# Body\n\nHere is some text with --- dashes in it.\n"
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {"name": "skill"}
        assert "dashes in it" in body


@pytest.mark.parametrize(
    ("content", "expected_frontmatter"),
    [
        ("", ({}, "")),
        ("no frontmatter", ({}, "no frontmatter")),
        ("---\nkey: val\n---\nbody", ({"key": "val"}, "body")),
    ],
    ids=["empty", "no-frontmatter", "simple"],
)
def test_parse_frontmatter_parametrized(content: str, expected_frontmatter: tuple):
    frontmatter, body = parse_frontmatter(content)
    expected_fm, expected_body = expected_frontmatter
    assert frontmatter == expected_fm
    assert body == expected_body
