"""Lint rules registry."""

from .base import LintRule
from .frontmatter import FrontmatterValidRule

# All available rules, instantiated and ready to use
ALL_RULES: list[LintRule] = [
    FrontmatterValidRule(),
]

# Map rule IDs to rules for --disable lookup
RULES_BY_ID: dict[str, LintRule] = {rule.rule_id: rule for rule in ALL_RULES}

__all__ = [
    "ALL_RULES",
    "RULES_BY_ID",
    "FrontmatterValidRule",
    "LintRule",
]
