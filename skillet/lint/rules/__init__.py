"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.naming import FilenameCaseRule

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
    FilenameCaseRule(),
]

__all__ = ["ALL_RULES", "LintRule"]
