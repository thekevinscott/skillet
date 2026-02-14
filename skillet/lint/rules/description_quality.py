"""LLM-assisted lint rule for description and instruction quality."""

from pathlib import Path

from pydantic import BaseModel, Field

from skillet._internal.sdk import query_structured
from skillet.lint.rules.base import LintRule
from skillet.lint.types import LintFinding, LintSeverity, SkillDocument
from skillet.prompts import load_prompt

PROMPT_PATH = Path(__file__).parent / "description_quality.txt"

MAX_BODY_CHARS = 2000


class QualityCheck(BaseModel):
    """Structured output for description quality analysis."""

    description_has_what: bool = Field(description="Description explains what the skill does")
    description_has_what_reason: str = Field(default="", description="Brief explanation")
    description_has_when: bool = Field(description="Description explains when to use the skill")
    description_has_when_reason: str = Field(default="", description="Brief explanation")
    description_has_triggers: bool = Field(
        description="Description includes specific trigger phrases"
    )
    description_has_triggers_reason: str = Field(default="", description="Brief explanation")
    description_mentions_file_types: bool = Field(
        description="Description mentions relevant file types (or skill is generic)"
    )
    description_mentions_file_types_reason: str = Field(default="", description="Brief explanation")
    instructions_are_specific: bool = Field(description="Instructions are specific and actionable")
    instructions_are_specific_reason: str = Field(default="", description="Brief explanation")


class DescriptionQualityRule(LintRule):
    """LLM-assisted check for description and instruction quality."""

    name = "description-quality"
    description = (
        "Description should explain what/when/triggers; "
        "instructions should be specific (LLM-assisted)"
    )

    def check(self, doc: SkillDocument) -> list[LintFinding]:  # noqa: ARG002
        """Sync stub — use check_async for LLM-assisted analysis."""
        return []

    async def check_async(self, doc: SkillDocument) -> list[LintFinding]:
        """Run LLM-assisted quality analysis on the skill."""
        skill_name = doc.frontmatter.get("name", "unknown")
        skill_description = str(doc.frontmatter.get("description", ""))
        body_preview = doc.body[:MAX_BODY_CHARS]

        if not skill_description and not body_preview.strip():
            return []

        prompt = load_prompt(
            PROMPT_PATH,
            name=skill_name,
            description=skill_description,
            body=body_preview,
        )

        result = await query_structured(
            prompt,
            QualityCheck,
            max_turns=1,
            allowed_tools=[],
        )

        findings = []
        checks = [
            (
                result.description_has_what,
                result.description_has_what_reason,
                "Description should explain WHAT the skill does",
            ),
            (
                result.description_has_when,
                result.description_has_when_reason,
                "Description should explain WHEN to use the skill",
            ),
            (
                result.description_has_triggers,
                result.description_has_triggers_reason,
                "Description should include specific trigger phrases",
            ),
            (
                result.description_mentions_file_types,
                result.description_mentions_file_types_reason,
                "Description should mention relevant file types if applicable",
            ),
            (
                result.instructions_are_specific,
                result.instructions_are_specific_reason,
                "Instructions should be specific and actionable",
            ),
        ]

        for passed, reason, message in checks:
            if not passed:
                detail = f"{message}: {reason}" if reason else message
                findings.append(
                    LintFinding(
                        rule=self.name,
                        message=detail,
                        severity=LintSeverity.WARNING,
                    )
                )

        return findings
