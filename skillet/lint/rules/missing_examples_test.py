"""Tests for missing examples rule."""

from pathlib import Path

from skillet.lint.rules.missing_examples import MissingExamplesRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(body: str, frontmatter_end_line: int = 4) -> SkillDocument:
    """Create a SkillDocument with body content."""
    return SkillDocument(
        path=Path("/test/SKILL.md"),
        content=body,
        frontmatter={"name": "test", "description": "test"},
        body=body,
        line_count=len(body.splitlines()),
        frontmatter_end_line=frontmatter_end_line,
    )


def describe_missing_examples_rule():
    """Tests for MissingExamplesRule."""

    def it_passes_when_no_goals_section():
        rule = MissingExamplesRule()
        doc = make_doc("# Instructions\nDo things.")

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_passes_for_goals_with_code_blocks():
        rule = MissingExamplesRule()
        doc = make_doc(
            "# Goals\n\n"
            "Parse JSON data.\n\n"
            "```python\ndata = json.loads(text)\n```"
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_passes_for_goals_with_example_keyword():
        rule = MissingExamplesRule()
        doc = make_doc(
            "# Goals\n\n"
            "Parse data. For example, use json.loads()."
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_passes_for_goals_with_key_value_patterns():
        rule = MissingExamplesRule()
        doc = make_doc(
            "# Goals\n\n"
            "- Input: raw text\n"
            "- Output: parsed data"
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_suggests_examples_for_bare_goals():
        rule = MissingExamplesRule()
        doc = make_doc(
            "# Goals\n\n"
            "- Parse JSON data\n"
            "- Validate input\n"
            "- Return results"
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.SUGGESTION
        assert "example" in findings[0].message.lower()

    def it_handles_goal_singular():
        rule = MissingExamplesRule()
        doc = make_doc(
            "# Goal\n\n"
            "Do one thing well."
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].rule_id == "missing-examples"

    def it_provides_suggestions():
        rule = MissingExamplesRule()
        doc = make_doc("# Goals\n\nBare goals.")

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].suggestion is not None
        assert "example" in findings[0].suggestion.lower()
