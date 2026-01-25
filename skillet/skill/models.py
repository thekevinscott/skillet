"""Pydantic models for skill operations."""

from pydantic import BaseModel, Field


class SkillContent(BaseModel):
    """Structured output for skill generation/improvement."""

    content: str = Field(description="The complete SKILL.md content in markdown format")
