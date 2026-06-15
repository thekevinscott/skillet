"""Summarize eval failures."""

from pathlib import Path

import yaml

from skillet._internal.agent import query_structured_via_agent
from skillet._internal.text import summarize_failure_for_eval
from skillet.agent import Agent
from skillet.eval.evaluate.result import IterationResult
from skillet.prompts import load_prompt

from .models import Summary

SUMMARIZE_PROMPT = Path(__file__).parent / "summarize.txt"


async def summarize_responses(results: list[IterationResult], agent: Agent) -> str:
    """Summarize what the agent actually did across failed responses."""
    response_summaries = [summarize_failure_for_eval(r.to_dict()) for r in results]
    responses_yaml = yaml.dump(response_summaries, default_flow_style=False)

    prompt = load_prompt(SUMMARIZE_PROMPT, responses_yaml=responses_yaml)

    result = await query_structured_via_agent(prompt, Summary, agent)
    return "\n".join(f"- {bullet}" for bullet in result.bullets)
