"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.naming import (
    FilenameCaseRule,
    FolderKebabCaseRule,
    NameKebabCaseRule,
    NameMatchesFolderRule,
    NameNoReservedRule,
)

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
    FilenameCaseRule(),
    FolderKebabCaseRule(),
    NameKebabCaseRule(),
    NameMatchesFolderRule(),
    NameNoReservedRule(),
]

__all__ = ["ALL_RULES", "LintRule"]
