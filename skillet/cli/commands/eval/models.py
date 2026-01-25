"""Pydantic models for eval command outputs."""

from pydantic import BaseModel, Field


class Summary(BaseModel):
    """Structured output for eval failure summarization."""

    bullets: list[str] = Field(
        description="2-4 bullet points summarizing patterns in failed responses. "
        "Each bullet should describe a behavior pattern with approximate percentage."
    )
