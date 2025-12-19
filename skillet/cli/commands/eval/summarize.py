"""Summarize eval failures."""

import yaml

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import summarize_failure_for_eval


async def summarize_responses(results: list[dict]) -> str:
    """Summarize what Claude actually did across failed responses."""
    response_summaries = [summarize_failure_for_eval(r) for r in results]

    responses_yaml = yaml.dump(response_summaries, default_flow_style=False)
    summary_prompt = f"""Analyze these AI responses that failed to meet expectations.
Summarize the PATTERNS in what the AI did instead.

## Failed Responses

{responses_yaml}

## Your Task

Write 2-4 bullet points summarizing what the AI typically did instead of expected.
Be specific and concise. Format as: - Pattern description (X% of responses)

Focus on the FORMAT or BEHAVIOR patterns, not the content quality.
"""

    return await query_assistant_text(summary_prompt, max_turns=1, allowed_tools=[])
