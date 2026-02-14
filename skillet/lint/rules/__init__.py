"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.structure import (
    BodyWordCountRule,
    DescriptionLengthRule,
    FrontmatterDelimitersRule,
    FrontmatterNoXmlRule,
    NoReadmeRule,
)

ALL_RULES: list[LintRule] = [
    FrontmatterDelimitersRule(),
    FrontmatterRule(),
    FrontmatterNoXmlRule(),
    DescriptionLengthRule(),
    NoReadmeRule(),
    BodyWordCountRule(),
]

LLM_RULES: list[LintRule] = []

__all__ = ["ALL_RULES", "LLM_RULES", "LintRule"]
