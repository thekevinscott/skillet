"""LLM-as-judge for evaluating responses against expected behavior."""

from pathlib import Path

from skillet.agent import Agent
from skillet.prompts import load_prompt

from .format_prompt import format_prompt
from .format_tool_calls import format_tool_calls
from .judge_via_agent import judge_via_agent

JUDGE_PROMPT = Path(__file__).parent / "judge.txt"


async def judge_response(
    prompt: str | list[str],
    response: str,
    expected: str,
    tool_calls: list[dict] | None = None,
    *,
    agent: Agent,
) -> dict:
    """Use the selected agent as a judge to evaluate if a response meets expectations.

    The verdict is produced by ``agent``'s own CLI. A judge that cannot return a
    valid verdict raises (``JudgeError``), failing the eval loudly rather than
    silently grading it as a pass.
    """
    formatted_prompt = format_prompt(prompt)
    formatted_tools = format_tool_calls(tool_calls or [])

    judge_prompt = load_prompt(
        JUDGE_PROMPT,
        prompt=formatted_prompt,
        response=response,
        tools=formatted_tools,
        expected=expected,
    )

    judgment = await judge_via_agent(judge_prompt, agent)
    return {
        "pass": judgment.passed,
        "reasoning": judgment.reasoning,
    }
