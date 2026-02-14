"""Tests for field presence lint rules."""

from pathlib import Path

import pytest

from skillet.lint.rules.fields import (
    CompatibilityFieldRule,
    LicenseFieldRule,
    MetadataFieldRule,
)
from skillet.lint.types import SkillDocument


def _doc(frontmatter: dict | None = None) -> SkillDocument:
    if frontmatter is None:
        frontmatter = {"name": "test", "description": "A skill."}
    return SkillDocument(
        path=Path("my-skill/SKILL.md"), content="", frontmatter=frontmatter, body=""
    )


@pytest.mark.parametrize(
    "rule_cls,field",
    [
        (LicenseFieldRule, "license"),
        (CompatibilityFieldRule, "compatibility"),
        (MetadataFieldRule, "metadata"),
    ],
)
def describe_field_rules():
    def it_passes_when_field_present(rule_cls, field):
        fm = {"name": "test", "description": "A skill.", field: "value"}
        assert rule_cls().check(_doc(fm)) == []

    def it_warns_when_field_missing(rule_cls, field):
        findings = rule_cls().check(_doc())
        assert len(findings) == 1
        assert findings[0].rule == f"field-{field}"
        assert field in findings[0].message
