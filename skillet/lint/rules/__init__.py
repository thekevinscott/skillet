"""Lint rule registry."""

from skillet.lint.rules.base import LintRule
from skillet.lint.rules.description_quality import DescriptionQualityRule
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
    FrontmatterDelimitersRule(),
    FrontmatterRule(),
    FrontmatterNoXmlRule(),
    FilenameCaseRule(),
    FolderKebabCaseRule(),
    NameKebabCaseRule(),
    NameMatchesFolderRule(),
    NameNoReservedRule(),
    DescriptionLengthRule(),
    NoReadmeRule(),
    BodyWordCountRule(),
    LicenseFieldRule(),
    CompatibilityFieldRule(),
    MetadataFieldRule(),
]

LLM_RULES: list[LintRule] = [
    DescriptionQualityRule(),
]

__all__ = ["ALL_RULES", "LLM_RULES", "LintRule"]
