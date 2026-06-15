"""Tests for the SKILL.md linter types."""

from pathlib import Path

from skillet.lint.types import LintFinding, LintResult, LintSeverity, SkillDocument


def describe_lint_severity():
    def it_has_warning_and_error_values():
        assert LintSeverity.WARNING.value == "warning"
        assert LintSeverity.ERROR.value == "error"


def describe_lint_finding():
    def it_constructs_with_required_fields():
        finding = LintFinding(rule="name", message="bad name", severity=LintSeverity.ERROR)
        assert finding.rule == "name"
        assert finding.message == "bad name"
        assert finding.severity is LintSeverity.ERROR
        assert finding.line is None

    def it_accepts_a_line_number():
        finding = LintFinding(rule="name", message="bad", severity=LintSeverity.WARNING, line=12)
        assert finding.line == 12


def describe_lint_result():
    def it_defaults_findings_to_an_empty_list():
        result = LintResult(path=Path("SKILL.md"))
        assert result.path == Path("SKILL.md")
        assert result.findings == []

    def it_uses_independent_default_lists():
        a = LintResult(path=Path("a.md"))
        b = LintResult(path=Path("b.md"))
        a.findings.append(LintFinding(rule="r", message="m", severity=LintSeverity.ERROR))
        assert b.findings == []


def describe_skill_document():
    def it_holds_parsed_frontmatter_and_body():
        doc = SkillDocument(
            path=Path("SKILL.md"),
            content="raw",
            frontmatter={"name": "test"},
            body="# Body",
        )
        assert doc.path == Path("SKILL.md")
        assert doc.content == "raw"
        assert doc.frontmatter["name"] == "test"
        assert doc.body == "# Body"
