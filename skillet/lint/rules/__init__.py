"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
]

__all__ = ["ALL_RULES", "LintRule"]
