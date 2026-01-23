"""Vague language detection rule."""

import re

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule

# Patterns to detect with suggested replacements
VAGUE_PATTERNS = [
    ("properly", "Specify what 'proper' means with concrete criteria"),
    ("correctly", "Define what 'correct' behavior looks like"),
    ("appropriately", "State the specific appropriateness criteria"),
    ("as needed", "List the conditions that determine the need"),
    ("as required", "Specify the requirements explicitly"),
    ("as necessary", "Define when it becomes necessary"),
    ("etc", "List all relevant items instead of using 'etc'"),
    ("and so on", "Enumerate the complete list"),
    ("and more", "Be explicit about what else is included"),
    ("if applicable", "State when it applies"),
    ("when possible", "Define the conditions for possibility"),
    ("as appropriate", "Specify the appropriateness criteria"),
]


class VagueLanguageRule(LintRule):
    """Detects vague or imprecise language in skills."""

    @property
    def rule_id(self) -> str:
        return "vague-language"

    @property
    def description(self) -> str:
        return "Flags vague terms like 'properly', 'correctly', 'as needed', 'etc.'"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []
        lines = doc.content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip frontmatter lines
            if line_num <= doc.frontmatter_end_line:
                continue

            line_lower = line.lower()
            for pattern, suggestion in VAGUE_PATTERNS:
                # Use word boundaries to avoid partial matches
                if re.search(rf"\b{re.escape(pattern)}\b", line_lower):
                    findings.append(
                        LintFinding(
                            rule_id=self.rule_id,
                            message=f"Vague language: '{pattern}'",
                            severity=LintSeverity.WARNING,
                            line=line_num,
                            suggestion=suggestion,
                        )
                    )

        return findings
