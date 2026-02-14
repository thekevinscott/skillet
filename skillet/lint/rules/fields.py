"""Lint rules for recommended frontmatter fields."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


def _field_rule(field_name: str) -> type[LintRule]:
    """Create a lint rule class that checks for a recommended field."""

    class FieldRule(LintRule):
        name = f"field-{field_name}"
        description = f"Recommended field '{field_name}' should be present"

        def check(self, doc: SkillDocument) -> list[LintFinding]:
            if field_name not in doc.frontmatter:
                return [
                    LintFinding(
                        rule=self.name,
                        message=f"Missing recommended field: {field_name}",
                        severity=LintSeverity.WARNING,
                    )
                ]
            return []

    FieldRule.__name__ = f"{field_name.capitalize()}FieldRule"
    FieldRule.__qualname__ = FieldRule.__name__
    FieldRule.__doc__ = f"Check that '{field_name}' field is present in frontmatter."
    return FieldRule


LicenseFieldRule = _field_rule("license")
CompatibilityFieldRule = _field_rule("compatibility")
MetadataFieldRule = _field_rule("metadata")
