"""Tests for extract_section_items."""

import pytest

from .extract_section_items import extract_section_items


def describe_extract_section_items():
    """Tests for extract_section_items function."""

    def it_extracts_numbered_items():
        body = "\n## Goals\n\n1. First goal\n2. Second goal\n3. Third goal\n\n## Next Section\n"
        items = extract_section_items(body, "goals")

        assert items == ["First goal", "Second goal", "Third goal"]

    def it_extracts_bulleted_items_with_dashes():
        body = "\n## Prohibitions\n\n- Don't do this\n- Don't do that\n"
        items = extract_section_items(body, "prohibitions")

        assert items == ["Don't do this", "Don't do that"]

    def it_extracts_bulleted_items_with_asterisks():
        body = "\n## Notes\n\n* Note one\n* Note two\n"
        items = extract_section_items(body, "notes")

        assert items == ["Note one", "Note two"]

    def it_is_case_insensitive():
        body = "\n## GOALS\n\n1. My goal\n"
        items = extract_section_items(body, "goals")

        assert items == ["My goal"]

    def it_returns_empty_for_missing_section():
        body = "\n## Other Section\n\n1. Item\n"
        items = extract_section_items(body, "goals")

        assert items == []

    def it_stops_at_next_section():
        body = "\n## Goals\n\n1. Goal one\n2. Goal two\n\n## Prohibitions\n\n1. Prohibition one\n"
        items = extract_section_items(body, "goals")

        assert items == ["Goal one", "Goal two"]

    def it_handles_section_at_end_of_document():
        body = "\n## Goals\n\n1. Final goal\n"
        items = extract_section_items(body, "goals")

        assert items == ["Final goal"]

    def it_prefers_numbered_over_bulleted():
        body = "\n## Goals\n\n1. Numbered item\n- Bulleted item\n"
        items = extract_section_items(body, "goals")

        assert items == ["Numbered item"]

    def it_handles_empty_section():
        body = "\n## Goals\n\n## Next Section\n"
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
