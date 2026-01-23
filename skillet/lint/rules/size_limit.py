"""Size limit validation rule."""

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule

WARNING_THRESHOLD = 400
ERROR_THRESHOLD = 500


class SizeLimitRule(LintRule):
    """Checks if skill file exceeds recommended size limits."""

    @property
    def rule_id(self) -> str:
        return "size-limit"

    @property
    def description(self) -> str:
        return f"Warns at {WARNING_THRESHOLD} lines, errors at {ERROR_THRESHOLD} lines"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []

        if doc.line_count >= ERROR_THRESHOLD:
            msg = (
                f"Skill file is {doc.line_count} lines "
                f"(exceeds {ERROR_THRESHOLD} line limit)"
            )
            findings.append(
                LintFinding(
                    rule_id=self.rule_id,
                    message=msg,
                    severity=LintSeverity.ERROR,
                    suggestion="Consider breaking into smaller, focused skills",
                )
            )
        elif doc.line_count >= WARNING_THRESHOLD:
            msg = (
                f"Skill file is {doc.line_count} lines "
                f"(approaching {ERROR_THRESHOLD} line limit)"
            )
            findings.append(
                LintFinding(
                    rule_id=self.rule_id,
                    message=msg,
                    severity=LintSeverity.WARNING,
                    suggestion="Consider simplifying or splitting the skill",
                )
            )

        return findings
