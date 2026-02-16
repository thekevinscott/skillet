"""Lint rule registry."""

from skillet.lint.rules.base import AsyncLintRule, LintRule
from skillet.lint.rules.body_word_count import BodyWordCountRule
from skillet.lint.rules.description_length import DescriptionLengthRule
from skillet.lint.rules.fields import (
    CompatibilityFieldRule,
    LicenseFieldRule,
    MetadataFieldRule,
)
from skillet.lint.rules.filename_case import FilenameCaseRule
from skillet.lint.rules.folder_kebab_case import FolderKebabCaseRule
from skillet.lint.rules.frontmatter import FrontmatterRule
from skillet.lint.rules.frontmatter_delimiters import FrontmatterDelimitersRule
from skillet.lint.rules.frontmatter_no_xml import FrontmatterNoXmlRule
from skillet.lint.rules.name_kebab_case import NameKebabCaseRule
from skillet.lint.rules.name_matches_folder import NameMatchesFolderRule
from skillet.lint.rules.name_no_reserved import NameNoReservedRule
from skillet.lint.rules.no_readme import NoReadmeRule

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
