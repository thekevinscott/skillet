"""Tests for the lint rule base classes."""

from pathlib import Path

import pytest

from skillet.lint.rules.base import AsyncLintRule, LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

_DOC = SkillDocument(path=Path("SKILL.md"), content="", frontmatter={}, body="")


class _ConcreteRule(LintRule):
    @property
    def name(self) -> str:
        return "my-rule"

    @property
    def description(self) -> str:
        return "checks something"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        return [
            LintFinding(
                rule=self.name,
                message=f"checked {doc.path}",
                severity=LintSeverity.ERROR,
            )
        ]


class _ConcreteAsyncRule(AsyncLintRule):
    @property
    def name(self) -> str:
        return "async-rule"

    @property
    def description(self) -> str:
        return "checks something async"

    async def check(self, doc: SkillDocument) -> list[LintFinding]:
        return [
            LintFinding(
                rule=self.name,
                message=f"checked {doc.path}",
                severity=LintSeverity.WARNING,
            )
        ]


def describe_lint_rule():
    def it_derives_url_from_name():
        assert _ConcreteRule().url == "https://skillet.run/guides/linting#my-rule"

    def it_returns_findings_from_check():
        findings = _ConcreteRule().check(_DOC)
        assert len(findings) == 1
        assert findings[0].rule == "my-rule"
        assert findings[0].severity is LintSeverity.ERROR


def describe_async_lint_rule():
    def it_derives_url_from_name():
        assert _ConcreteAsyncRule().url == "https://skillet.run/guides/linting#async-rule"

    @pytest.mark.asyncio
    async def it_returns_findings_from_async_check():
        findings = await _ConcreteAsyncRule().check(_DOC)
        assert len(findings) == 1
        assert findings[0].severity is LintSeverity.WARNING
