"""Tests for description quality LLM-assisted lint rule."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.lint.rules.description_quality import (
    DescriptionQualityRule,
    QualityCheck,
)
from skillet.lint.types import LintSeverity, SkillDocument


def _doc(
    name: str = "my-skill",
    description: str = "A skill.",
    body: str = "# Instructions\n\nDo the thing.",
) -> SkillDocument:
    return SkillDocument(
        path=Path("my-skill/SKILL.md"),
        content=f"---\nname: {name}\ndescription: {description}\n---\n{body}",
        frontmatter={"name": name, "description": description},
        body=body,
    )


def describe_description_quality_rule():
    rule = DescriptionQualityRule()

    @pytest.fixture(autouse=True)
    def mock_query_structured():
        with patch(
            "skillet.lint.rules.description_quality.query_structured",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = QualityCheck(
                description_has_what=True,
                description_has_when=True,
                description_has_triggers=True,
                description_mentions_file_types=True,
                instructions_are_specific=True,
            )
            yield mock

    def it_returns_nothing_from_sync_check():
        findings = rule.check(_doc())
        assert findings == []

    @pytest.mark.asyncio
    async def it_passes_when_all_checks_pass(mock_query_structured):
        findings = await rule.check_async(_doc())
        assert findings == []
        mock_query_structured.assert_called_once()

    @pytest.mark.asyncio
    async def it_warns_when_description_missing_what(mock_query_structured):
        mock_query_structured.return_value = QualityCheck(
            description_has_what=False,
            description_has_what_reason="No explanation of what the skill does",
            description_has_when=True,
            description_has_triggers=True,
            description_mentions_file_types=True,
            instructions_are_specific=True,
        )
        findings = await rule.check_async(_doc())
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "description-quality"
        assert "WHAT" in findings[0].message

    @pytest.mark.asyncio
    async def it_warns_on_multiple_failures(mock_query_structured):
        mock_query_structured.return_value = QualityCheck(
            description_has_what=False,
            description_has_what_reason="Missing",
            description_has_when=False,
            description_has_when_reason="Missing",
            description_has_triggers=False,
            description_has_triggers_reason="Missing",
            description_mentions_file_types=True,
            instructions_are_specific=False,
            instructions_are_specific_reason="Too vague",
        )
        findings = await rule.check_async(_doc())
        assert len(findings) == 4

    @pytest.mark.asyncio
    async def it_skips_when_no_description_or_body(mock_query_structured):
        doc = SkillDocument(
            path=Path("my-skill/SKILL.md"),
            content="---\nname: x\n---\n",
            frontmatter={"name": "x"},
            body="",
        )
        findings = await rule.check_async(doc)
        assert findings == []
        mock_query_structured.assert_not_called()
