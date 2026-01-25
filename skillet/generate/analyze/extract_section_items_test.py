"""Tests for extract_section_items."""

import pytest

from .extract_section_items import extract_section_items


def describe_extract_section_items():
    """Tests for extract_section_items function."""

    def it_extracts_numbered_items():
        body = """
## Goals

1. First goal
2. Second goal
3. Third goal

## Next Section
"""
        items = extract_section_items(body, "goals")

        assert items == ["First goal", "Second goal", "Third goal"]

    def it_extracts_bulleted_items_with_dashes():
        body = """
## Prohibitions

- Don't do this
- Don't do that
"""
        items = extract_section_items(body, "prohibitions")

        assert items == ["Don't do this", "Don't do that"]

    def it_extracts_bulleted_items_with_asterisks():
        body = """
## Notes

* Note one
* Note two
"""
        items = extract_section_items(body, "notes")

        assert items == ["Note one", "Note two"]

    def it_is_case_insensitive():
        body = """
## GOALS

1. My goal
"""
        items = extract_section_items(body, "goals")

        assert items == ["My goal"]

    def it_returns_empty_for_missing_section():
        body = """
## Other Section

1. Item
"""
        items = extract_section_items(body, "goals")

        assert items == []

    def it_stops_at_next_section():
        body = """
## Goals

1. Goal one
2. Goal two

## Prohibitions

1. Prohibition one
"""
        items = extract_section_items(body, "goals")

        assert items == ["Goal one", "Goal two"]

    def it_handles_section_at_end_of_document():
        body = """
## Goals

1. Final goal
"""
        items = extract_section_items(body, "goals")

        assert items == ["Final goal"]

    def it_prefers_numbered_over_bulleted():
        body = """
## Goals

1. Numbered item
- Bulleted item
"""
        items = extract_section_items(body, "goals")

        assert items == ["Numbered item"]

    def it_handles_empty_section():
        body = """
## Goals

## Next Section
"""
        items = extract_section_items(body, "goals")

        assert items == []


@pytest.mark.parametrize(
    ("body", "section", "expected"),
    [
        ("## Goals\n1. Item", "goals", ["Item"]),
        ("## goals\n1. Item", "Goals", ["Item"]),
        ("No section", "goals", []),
        ("## Goals\n- A\n- B", "goals", ["A", "B"]),
    ],
    ids=["numbered", "case-mismatch", "missing", "bulleted"],
)
def test_extract_section_items_parametrized(body: str, section: str, expected: list[str]):
    assert extract_section_items(body, section) == expected
