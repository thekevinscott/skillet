"""Tests for lint_skill."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.errors import LintError
from skillet.lint.lint_skill import lint_skill
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

VALID_SKILL = """\
---
name: x
description: y
---
"""

EMPTY_FRONTMATTER_SKILL = """\
---
---
"""


def describe_lint_skill():
    @pytest.fixture(autouse=True)
    def mock_parse_skill():
        with patch("skillet.lint.lint_skill.parse_skill") as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_all_rules():
        rules: list = []
        with patch("skillet.lint.lint_skill.ALL_RULES", rules):
            yield rules

    @pytest.fixture(autouse=True)
    def mock_llm_rules():
        rules: list = []
        with patch("skillet.lint.lint_skill.LLM_RULES", rules):
            yield rules

    @pytest.mark.asyncio
    async def it_raises_lint_error_for_missing_file(tmp_path: Path):
        with pytest.raises(LintError, match="File not found"):
            await lint_skill(tmp_path / "nonexistent.md")

    @pytest.mark.asyncio
    async def it_returns_empty_findings_for_valid_skill(tmp_path: Path, mock_parse_skill):
        skill = tmp_path / "SKILL.md"
        skill.write_text(VALID_SKILL)

        mock_parse_skill.return_value = SkillDocument(
            path=skill, content="", frontmatter={"name": "x"}, body=""
        )

        result = await lint_skill(skill)

        assert result.findings == []
        assert result.path == skill

    @pytest.mark.asyncio
    async def it_collects_findings_from_rules(tmp_path: Path, mock_parse_skill, mock_all_rules):
        skill = tmp_path / "SKILL.md"
        skill.write_text(EMPTY_FRONTMATTER_SKILL)

        mock_parse_skill.return_value = SkillDocument(
            path=skill, content="", frontmatter={}, body=""
        )
        finding = LintFinding(rule="test-rule", message="test", severity=LintSeverity.WARNING)
        mock_all_rules.append(type("MockRule", (), {"check": lambda _self, _doc: [finding]})())

        result = await lint_skill(skill)

        assert len(result.findings) == 1
        assert result.findings[0].rule == "test-rule"

    @pytest.mark.asyncio
    async def it_runs_llm_rules_by_default(
        tmp_path: Path, mock_parse_skill, mock_llm_rules
    ):
        skill = tmp_path / "SKILL.md"
        skill.write_text(VALID_SKILL)

        mock_parse_skill.return_value = SkillDocument(
            path=skill, content="", frontmatter={"name": "x"}, body=""
        )
        finding = LintFinding(rule="llm-rule", message="llm issue", severity=LintSeverity.WARNING)
        mock_rule = AsyncMock()
        mock_rule.check.return_value = [finding]
        mock_llm_rules.append(mock_rule)

        result = await lint_skill(skill)

        assert len(result.findings) == 1
        assert result.findings[0].rule == "llm-rule"

    @pytest.mark.asyncio
    async def it_skips_llm_rules_when_include_llm_is_false(
        tmp_path: Path, mock_parse_skill, mock_llm_rules
    ):
        skill = tmp_path / "SKILL.md"
        skill.write_text(VALID_SKILL)

        mock_parse_skill.return_value = SkillDocument(
            path=skill, content="", frontmatter={"name": "x"}, body=""
        )
        mock_rule = AsyncMock()
        mock_rule.check.return_value = [
            LintFinding(rule="llm-rule", message="llm issue", severity=LintSeverity.WARNING)
        ]
        mock_llm_rules.append(mock_rule)

        result = await lint_skill(skill, include_llm=False)

        assert result.findings == []
        mock_rule.check.assert_not_called()
