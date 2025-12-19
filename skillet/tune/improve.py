"""Improve a skill based on failures."""

from pathlib import Path

import yaml

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import strip_markdown, summarize_failure_for_tuning
from skillet.config import MAX_SKILL_LINES
from skillet.prompts import load_prompt

IMPROVE_PROMPT = Path(__file__).parent / "improve.txt"

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


def get_skill_file(skill_path: Path) -> Path:
    """Get the skill file path, handling both directory and file inputs.

    Args:
        skill_path: Path to skill directory or direct .md file

    Returns:
        Path to the actual skill file
    """
    if skill_path.is_file():
        return skill_path
    return skill_path / "SKILL.md"


async def improve_skill(
    skill_path: Path,
    failures: list[dict],
    tip: str | None = None,
) -> str:
    """Use Claude to improve the skill file based on failures.

    Args:
        skill_path: Path to skill directory or direct .md file
        failures: List of failed evaluation results
        tip: Optional style tip for improvement

    Returns:
        New skill content
    """
    skill_file = get_skill_file(skill_path)
    current_skill = skill_file.read_text()

    # Summarize failures
    failure_summary = [summarize_failure_for_tuning(f) for f in failures]
    failures_yaml = yaml.dump(failure_summary, default_flow_style=False)
    tip_section = f"- Style tip: {tip}\n" if tip else ""

    prompt = load_prompt(
        IMPROVE_PROMPT,
        current_skill=current_skill,
        failures_yaml=failures_yaml,
        max_lines=str(MAX_SKILL_LINES),
        tip_section=tip_section,
    )

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    result = strip_markdown(result)

    # Hard limit: truncate to MAX_SKILL_LINES if still too long
    lines = result.split("\n")
    if len(lines) > MAX_SKILL_LINES:
        result = "\n".join(lines[:MAX_SKILL_LINES])

    return result
