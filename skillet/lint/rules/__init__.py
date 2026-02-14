"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
]

LLM_RULES: list[LintRule] = []

__all__ = ["ALL_RULES", "LLM_RULES", "LintRule"]
