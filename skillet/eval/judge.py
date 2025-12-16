"""LLM-as-judge for evaluating responses against expected behavior."""

import json

from skillet._internal.sdk import query_assistant_text


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
        expected: What the user expected (from the gap file)
        tool_calls: Optional list of tool calls made during the response

    Returns:
        dict with 'pass' (bool), 'reasoning' (str), and 'raw' (str)
    """
    formatted_prompt = format_prompt_for_judge(prompt)
    formatted_tools = format_tool_calls_for_judge(tool_calls or [])

    judge_prompt = f"""You are evaluating whether an AI response meets the user's expectations.

## Original Prompt
{formatted_prompt}

## AI Response
{response}

## Tools Used
{formatted_tools}

## Expected Behavior
{expected}

## Your Task
Determine if the AI response meets the expected behavior. Be strict but fair.
Consider both the text response AND the tools used when evaluating.

Respond in this exact format:
PASS: yes or no
REASONING: one sentence explanation
"""

    result = await query_assistant_text(judge_prompt, max_turns=1, allowed_tools=[])

    # Parse the response
    lines = result.strip().split("\n")
    pass_line = lines[0] if lines else ""
    reasoning_line = lines[1] if len(lines) > 1 else ""

    passed = "yes" in pass_line.lower()
    reasoning = reasoning_line.replace("REASONING:", "").strip()

    return {
        "pass": passed,
        "reasoning": reasoning,
        "raw": result,
    }
