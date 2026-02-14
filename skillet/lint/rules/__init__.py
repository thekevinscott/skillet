"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.naming import (
    FilenameCaseRule,
    FolderKebabCaseRule,
    NameKebabCaseRule,
)

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
    FilenameCaseRule(),
    FolderKebabCaseRule(),
    NameKebabCaseRule(),
]

__all__ = ["ALL_RULES", "LintRule"]
