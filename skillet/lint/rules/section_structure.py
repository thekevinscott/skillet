"""Section structure validation rule."""

import re

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule

RECOMMENDED_SECTIONS = ["Role", "Goals", "Instructions"]


class SectionStructureRule(LintRule):
    """Suggests standard section structure for skills."""

    @property
    def rule_id(self) -> str:
        return "section-structure"

    @property
    def description(self) -> str:
        return "Suggests including Role, Goals, and Instructions sections"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []

        # Find all markdown headers in the body
        headers = re.findall(r"^#+\s+(.+)$", doc.body, re.MULTILINE)
        header_names = [h.lower().strip() for h in headers]

        for section in RECOMMENDED_SECTIONS:
            if section.lower() not in header_names:
                findings.append(
                    LintFinding(
                        rule_id=self.rule_id,
                        message=f"Missing recommended section: {section}",
                        severity=LintSeverity.SUGGESTION,
                        suggestion=f"Add a '## {section}' section",
                    )
                )

        return findings
