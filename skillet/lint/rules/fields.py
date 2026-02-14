"""Lint rules for recommended frontmatter fields."""

from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument


class LicenseFieldRule(LintRule):
    """Check that the license field is present."""

    name = "field-license"
    description = "Frontmatter should include a license field"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if "license" not in doc.frontmatter:
            return [
                LintFinding(
                    rule=self.name,
                    message="Missing recommended field: license",
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []


class CompatibilityFieldRule(LintRule):
    """Check that the compatibility field is present."""

    name = "field-compatibility"
    description = "Frontmatter should include a compatibility field"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if "compatibility" not in doc.frontmatter:
            return [
                LintFinding(
                    rule=self.name,
                    message="Missing recommended field: compatibility",
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []


class MetadataFieldRule(LintRule):
    """Check that the metadata field is present."""

    name = "field-metadata"
    description = "Frontmatter should include a metadata field"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        if "metadata" not in doc.frontmatter:
            return [
                LintFinding(
                    rule=self.name,
                    message="Missing recommended field: metadata",
                    severity=LintSeverity.WARNING,
                    line=1,
                )
            ]
        return []
