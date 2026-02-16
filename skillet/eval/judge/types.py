"""Type definitions for the judge module."""

from pydantic import BaseModel, ConfigDict, Field


class Judgment(BaseModel):
    """Structured output for judge responses."""

    model_config = ConfigDict(populate_by_name=True)

    passed: bool = Field(
        description="Whether the response meets the expected behavior",
        alias="pass",
    )
    reasoning: str = Field(
        default="",
        description="One sentence explanation of the judgment",
    )
