"""Dangling reference detection rule."""

import re

from skillet.lint.types import LintFinding, LintSeverity, SkillDocument

from .base import LintRule


class DanglingReferenceRule(LintRule):
    """Detects references to files that don't exist."""

    @property
    def rule_id(self) -> str:
        return "dangling-reference"

    @property
    def description(self) -> str:
        return "Checks for references to non-existent files"

    def check(self, doc: SkillDocument) -> list[LintFinding]:
        findings = []
        lines = doc.content.splitlines()
        skill_dir = doc.path.parent

        for line_num, line in enumerate(lines, start=1):
            # Skip frontmatter lines
            if line_num <= doc.frontmatter_end_line:
                continue

            # Find markdown link references [text](path)
            for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                ref_path = match.group(2)  # The path is in group 2

                # Skip URLs and anchors
                if ref_path.startswith(("http://", "https://", "#", "mailto:")):
                    continue

                # Resolve relative to skill directory
                resolved = skill_dir / ref_path

                if not resolved.exists():
                    findings.append(
                        LintFinding(
                            rule_id=self.rule_id,
                            message=f"Reference to non-existent file: {ref_path}",
                            severity=LintSeverity.WARNING,
                            line=line_num,
                            suggestion="Create the file or update the reference",
                        )
                    )

            # Find backtick path references `file.ext`
            for match in re.finditer(r"`([^`]+\.\w+)`", line):
                ref_path = match.group(1)

                # Skip URLs and anchors
                if ref_path.startswith(("http://", "https://", "#", "mailto:")):
                    continue

                # Resolve relative to skill directory
                resolved = skill_dir / ref_path

                if not resolved.exists():
                    findings.append(
                        LintFinding(
                            rule_id=self.rule_id,
                            message=f"Reference to non-existent file: {ref_path}",
                            severity=LintSeverity.WARNING,
                            line=line_num,
                            suggestion="Create the file or update the reference",
                        )
                    )

        return findings
