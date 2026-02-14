"""Lint rule registry."""

from skillet.lint.rules.base import AsyncLintRule, LintRule
from skillet.lint.rules.fields import (
    CompatibilityFieldRule,
    LicenseFieldRule,
    MetadataFieldRule,
)
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.naming import (
    FilenameCaseRule,
    FolderKebabCaseRule,
    NameKebabCaseRule,
    NameMatchesFolderRule,
    NameNoReservedRule,
)
from skillet.lint.rules.structure import (
    BodyWordCountRule,
    DescriptionLengthRule,
    FrontmatterDelimitersRule,
    FrontmatterNoXmlRule,
    NoReadmeRule,
)

ALL_RULES: list[LintRule] = [
    FrontmatterRule(),
    FrontmatterDelimitersRule(),
    FrontmatterNoXmlRule(),
    FilenameCaseRule(),
    FolderKebabCaseRule(),
    NameKebabCaseRule(),
    NameMatchesFolderRule(),
    NameNoReservedRule(),
    DescriptionLengthRule(),
    BodyWordCountRule(),
    NoReadmeRule(),
    LicenseFieldRule(),
    CompatibilityFieldRule(),
    MetadataFieldRule(),
]

LLM_RULES: list[AsyncLintRule] = []

__all__ = ["ALL_RULES", "LLM_RULES", "AsyncLintRule", "LintRule"]
