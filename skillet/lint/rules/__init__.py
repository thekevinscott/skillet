"""Lint rules registry."""

from .base import LintRule
from .dangling_reference import DanglingReferenceRule
from .frontmatter import FrontmatterValidRule
from .missing_examples import MissingExamplesRule
from .passive_voice import PassiveVoiceRule
from .section_structure import SectionStructureRule
from .size_limit import SizeLimitRule
from .vague_language import VagueLanguageRule

# All available rules, instantiated and ready to use
ALL_RULES: list[LintRule] = [
    FrontmatterValidRule(),
    SizeLimitRule(),
    SectionStructureRule(),
    VagueLanguageRule(),
    PassiveVoiceRule(),
    MissingExamplesRule(),
    DanglingReferenceRule(),
]

# Map rule IDs to rules for --disable lookup
RULES_BY_ID: dict[str, LintRule] = {rule.rule_id: rule for rule in ALL_RULES}

__all__ = [
    "ALL_RULES",
    "RULES_BY_ID",
    "DanglingReferenceRule",
    "FrontmatterValidRule",
    "LintRule",
    "MissingExamplesRule",
    "PassiveVoiceRule",
    "SectionStructureRule",
    "SizeLimitRule",
    "VagueLanguageRule",
]
