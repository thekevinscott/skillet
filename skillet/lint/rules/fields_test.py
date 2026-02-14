"""Tests for recommended field lint rules."""

from pathlib import Path

from skillet.lint.rules.fields import (
    CompatibilityFieldRule,
    LicenseFieldRule,
    MetadataFieldRule,
)
from skillet.lint.types import LintSeverity, SkillDocument


def _doc(frontmatter: dict | None = None) -> SkillDocument:
    if frontmatter is None:
        frontmatter = {
            "name": "x",
            "description": "y",
            "license": "MIT",
            "compatibility": ">=1.0",
            "metadata": {"author": "test"},
        }
    return SkillDocument(
        path=Path("my-skill/SKILL.md"),
        content="",
        frontmatter=frontmatter,
        body="",
    )


def describe_license_field_rule():
    rule = LicenseFieldRule()

    def it_passes_when_license_present():
        findings = rule.check(_doc({"license": "MIT"}))
        assert findings == []

    def it_warns_when_license_missing():
        findings = rule.check(_doc({}))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "field-license"


def describe_compatibility_field_rule():
    rule = CompatibilityFieldRule()

    def it_passes_when_compatibility_present():
        findings = rule.check(_doc({"compatibility": ">=1.0"}))
        assert findings == []

    def it_warns_when_compatibility_missing():
        findings = rule.check(_doc({}))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "field-compatibility"


def describe_metadata_field_rule():
    rule = MetadataFieldRule()

    def it_passes_when_metadata_present():
        findings = rule.check(_doc({"metadata": {"author": "test"}}))
        assert findings == []

    def it_warns_when_metadata_missing():
        findings = rule.check(_doc({}))
        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert findings[0].rule == "field-metadata"
