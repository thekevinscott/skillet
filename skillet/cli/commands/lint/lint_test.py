"""Tests for lint_command."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.commands.lint.lint import lint_command
from skillet.errors import LintError
from skillet.lint.types import LintFinding, LintResult, LintSeverity


def describe_lint_command():
    @pytest.fixture(autouse=True)
    def mock_lint_skill():
        with patch("skillet.cli.commands.lint.lint.lint_skill", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_console():
        with patch("skillet.cli.commands.lint.lint.console") as mock:
            yield mock

    @pytest.mark.asyncio
    async def it_exits_0_when_no_findings(mock_lint_skill):
        mock_lint_skill.return_value = LintResult(path=Path("SKILL.md"), findings=[])

        await lint_command(Path("SKILL.md"))  # Should not raise

    @pytest.mark.asyncio
    async def it_exits_1_when_findings_exist(mock_lint_skill):
        finding = LintFinding(rule="test", message="msg", severity=LintSeverity.WARNING)
        mock_lint_skill.return_value = LintResult(path=Path("SKILL.md"), findings=[finding])

        with pytest.raises(SystemExit) as exc:
            await lint_command(Path("SKILL.md"))
        assert exc.value.code == 1

    @pytest.mark.asyncio
    async def it_exits_2_on_lint_error(mock_lint_skill):
        mock_lint_skill.side_effect = LintError("File not found")

        with pytest.raises(SystemExit) as exc:
            await lint_command(Path("SKILL.md"))
        assert exc.value.code == 2

    @pytest.mark.asyncio
    async def it_prints_findings(mock_lint_skill, mock_console):
        finding = LintFinding(rule="test", message="msg", severity=LintSeverity.WARNING, line=5)
        mock_lint_skill.return_value = LintResult(path=Path("SKILL.md"), findings=[finding])

        with pytest.raises(SystemExit):
            await lint_command(Path("SKILL.md"))

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("SKILL.md:5" in c and "warning" in c for c in calls)

    @pytest.mark.asyncio
    async def it_passes_include_llm_to_lint_skill(mock_lint_skill):
        mock_lint_skill.return_value = LintResult(path=Path("SKILL.md"), findings=[])

        await lint_command(Path("SKILL.md"), include_llm=True)

        mock_lint_skill.assert_called_once_with(Path("SKILL.md"), include_llm=True)
