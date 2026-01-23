"""Passive voice detection rule."""

import re

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule

# Common passive voice patterns (verb to be + past participle)
PASSIVE_PATTERNS = [
    r"\bshould be (\w+ed|\w+en)\b",
    r"\bmust be (\w+ed|\w+en)\b",
    r"\bcan be (\w+ed|\w+en)\b",
    r"\bwill be (\w+ed|\w+en)\b",
    r"\bis (\w+ed|\w+en)\b",
    r"\bare (\w+ed|\w+en)\b",
    r"\bwas (\w+ed|\w+en)\b",
    r"\bwere (\w+ed|\w+en)\b",
    r"\bbeen (\w+ed|\w+en)\b",
]

# Common false positives to ignore
FALSE_POSITIVES = {
    "is expected",
    "are expected",
    "is used",
    "are used",
    "is called",
    "are called",
    "is named",
    "are named",
    "is defined",
    "are defined",
}


class PassiveVoiceRule(LintRule):
    """Detects passive voice that could be more direct."""

    @property
    def rule_id(self) -> str:
        return "passive-voice"

    @property
    def description(self) -> str:
        return "Flags passive voice constructions like 'should be handled'"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []
        lines = doc.content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip frontmatter lines
            if line_num <= doc.frontmatter_end_line:
                continue

            line_lower = line.lower()

            for pattern in PASSIVE_PATTERNS:
                matches = re.finditer(pattern, line_lower)
                for match in matches:
                    matched_text = match.group(0)
                    # Skip false positives
                    if matched_text in FALSE_POSITIVES:
                        continue

                    findings.append(
                        LintFinding(
                            rule_id=self.rule_id,
                            message=f"Passive voice: '{matched_text}'",
                            severity=LintSeverity.WARNING,
                            line=line_num,
                            suggestion="Rewrite in active voice with a clear subject",
                        )
                    )

        return findings
