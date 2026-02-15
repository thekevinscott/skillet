"""LLM-as-judge for evaluating responses against expected behavior."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from skillet._internal.sdk import StructuredOutputError, query_structured
from skillet.prompts import load_prompt

from .format_prompt import format_prompt
from .format_tool_calls import format_tool_calls

JUDGE_PROMPT = Path(__file__).parent / "judge.txt"


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


async def judge_response(
    prompt: str | list[str],
    response: str,
    expected: str,
    tool_calls: list[dict] | None = None,
) -> dict:
    """Use Claude as a judge to evaluate if a response meets expectations."""
    formatted_prompt = format_prompt(prompt)
    formatted_tools = format_tool_calls(tool_calls or [])

    judge_prompt = load_prompt(
        JUDGE_PROMPT,
        prompt=formatted_prompt,
        response=response,
        tools=formatted_tools,
        expected=expected,
    )

    try:
        judgment = await query_structured(
            judge_prompt,
            Judgment,
            max_turns=1,
            allowed_tools=[],
        )
        return {
            "pass": judgment.passed,
            "reasoning": judgment.reasoning,
        }
    except StructuredOutputError:
        # Canary triggered: structured output contained backticks
        raise
    except Exception as e:
        # Fallback: if parsing fails, treat as failure
        return {
            "pass": False,
            "reasoning": f"Failed to parse judge response: {e}",
        }
