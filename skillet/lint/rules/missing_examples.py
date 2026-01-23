"""Missing examples detection rule."""

import re

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule


class MissingExamplesRule(LintRule):
    """Checks for goals or instructions without examples."""

    @property
    def rule_id(self) -> str:
        return "missing-examples"

    @property
    def description(self) -> str:
        return "Suggests adding examples for goals and complex instructions"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []

        # Look for Goals section without examples
        goals_match = re.search(
            r"^#+\s*Goals?\s*$(.+?)(?=^#+|\Z)",
            doc.body,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )

        if goals_match:
            goals_content = goals_match.group(1)
            # Check if there are any code blocks or example markers
            # Check if there are code blocks, "example" keyword, or key-value patterns
            has_code_blocks = "```" in goals_content
            has_example_keyword = "example" in goals_content.lower()
            has_key_value = re.search(r"^\s*[-*]\s+.*:\s+", goals_content, re.MULTILINE)
            has_examples = has_code_blocks or has_example_keyword or has_key_value

            if not has_examples:
                # Find the line number of the Goals section
                body_lines = doc.body.splitlines()
                for i, line in enumerate(body_lines):
                    if re.match(r"^#+\s*Goals?\s*$", line, re.IGNORECASE):
                        findings.append(
                            LintFinding(
                                rule_id=self.rule_id,
                                message="Goals section without examples",
                                severity=LintSeverity.SUGGESTION,
                                line=doc.frontmatter_end_line + i + 1,
                                suggestion="Add concrete examples demonstrating each goal",
                            )
                        )
                        break

        return findings
