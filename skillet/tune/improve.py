"""Improve a skill based on failures."""

from pathlib import Path

import yaml

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import strip_markdown, summarize_failure_for_tuning
from skillet.config import MAX_SKILL_LINES

# Tips to explore instruction space (inspired by DSPy MIPROv2)
TUNE_TIPS = [
    "Be extremely terse - every word must earn its place",
    "Use imperatives: DO this, NEVER do that",
    "Focus on the trigger condition - when exactly should this activate?",
    "Emphasize what NOT to do - Claude defaults to asking permission",
    "Use bullet points, not paragraphs",
    "Put the most important instruction first",
    "Add a concrete example of correct behavior",
    "Make the description more specific about when to trigger",
    "Use CAPS for critical words like IMMEDIATELY, NEVER, MUST",
]


async def improve_skill(
    skill_path: Path,
    failures: list[dict],
    tip: str | None = None,
) -> str:
    """Use Claude to improve the SKILL.md based on failures.

    Args:
        skill_path: Path to skill directory
        failures: List of failed evaluation results
        tip: Optional style tip for improvement

    Returns:
        New SKILL.md content
    """
    current_skill = (skill_path / "SKILL.md").read_text()

    # Summarize failures
    failure_summary = [summarize_failure_for_tuning(f) for f in failures]

    prompt = f"""Improve this SKILL.md so Claude exhibits the expected behavior.

## Current SKILL.md

{current_skill}

## Failures

These prompts did NOT produce the expected behavior:

{yaml.dump(failure_summary, default_flow_style=False)}

## Your Task

Revise the SKILL.md to fix these failures. Common issues:
- Description not specific enough about WHEN to trigger
- Instructions not explicit enough (Claude defaults to asking permission)
- Missing "do NOT ask" or "IMMEDIATELY" language for automatic behaviors

IMPORTANT CONSTRAINTS:
- Keep the SKILL.md under {MAX_SKILL_LINES} lines total
- Be concise - shorter is better
- Replace verbose instructions with terse, direct ones
- Do NOT keep adding more text - rewrite to be minimal
{f"- Style tip: {tip}" if tip else ""}

Return ONLY the improved SKILL.md content (no explanation, no code fences)."""

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    result = strip_markdown(result)

    # Hard limit: truncate to MAX_SKILL_LINES if still too long
    lines = result.split("\n")
    if len(lines) > MAX_SKILL_LINES:
        result = "\n".join(lines[:MAX_SKILL_LINES])

    return result
