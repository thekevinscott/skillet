"""Summarize eval failures."""

from pathlib import Path

import yaml

from skillet._internal.sdk import query_structured
from skillet._internal.text import summarize_failure_for_eval
from skillet.prompts import load_prompt

from .models import Summary

SUMMARIZE_PROMPT = Path(__file__).parent / "summarize.txt"


async def summarize_responses(results: list[dict]) -> str:
    """Summarize what Claude actually did across failed responses."""
    response_summaries = [summarize_failure_for_eval(r) for r in results]
    responses_yaml = yaml.dump(response_summaries, default_flow_style=False)

    prompt = load_prompt(SUMMARIZE_PROMPT, responses_yaml=responses_yaml)

    result = await query_structured(prompt, Summary, max_turns=1, allowed_tools=[])
    return "\n".join(f"- {bullet}" for bullet in result.bullets)
