"""LLM-as-judge for evaluating responses against expected behavior."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from skillet._internal.sdk import StructuredOutputError, query_structured
from skillet.prompts import load_prompt

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


def format_prompt_for_judge(prompt: str | list[str]) -> str:
    """Format prompt(s) for the judge, handling multi-turn conversations."""
    if isinstance(prompt, str):
        return prompt

    # Multi-turn: format as numbered conversation
    lines = []
    for i, p in enumerate(prompt, 1):
        lines.append(f"Turn {i}: {p}")
    return "\n".join(lines)


def format_tool_calls_for_judge(tool_calls: list[dict]) -> str:
    """Format tool calls for the judge prompt."""
    if not tool_calls:
        return "(no tools used)"

    lines = []
    for call in tool_calls:
        input_data = call.get("input", {})
        input_str = json.dumps(input_data, indent=2)
        lines.append(f"- {call['name']}: {input_str}")

    return "\n".join(lines)


async def judge_response(
    prompt: str | list[str],
    response: str,
    expected: str,
    tool_calls: list[dict] | None = None,
) -> dict:
    """Use Claude as a judge to evaluate if a response meets expectations.

    Args:
        prompt: The original user prompt, or list of prompts for multi-turn
        response: Claude's final response to evaluate
        expected: What the user expected (from the eval file)
        tool_calls: Optional list of tool calls made during the response

    Returns:
        dict with 'pass' (bool), 'reasoning' (str), and 'raw' (str)
    """
    formatted_prompt = format_prompt_for_judge(prompt)
    formatted_tools = format_tool_calls_for_judge(tool_calls or [])

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
