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


def _get_tune_improve_skill() -> str:
    """Load the tune-improve skill content.

    Looks for the skill in:
    1. Built .claude/commands/skillet/tune-improve.md (relative to this file)
    2. Template .claude-template/commands/skillet/tune-improve.md

    Returns:
        The skill content, or empty string if not found
    """
    # Find skillet package root
    package_root = Path(__file__).parent.parent.parent

    # Try built commands first
    built_path = package_root / ".claude" / "commands" / "skillet" / "tune-improve.md"
    if built_path.exists():
        return built_path.read_text()

    # Fall back to template
    template_path = package_root / ".claude-template" / "commands" / "skillet" / "tune-improve.md"
    if template_path.exists():
        return template_path.read_text()

    return ""


async def improve_skill(
    skill_path: Path,
    failures: list[dict],
    passes: list[dict] | None = None,
    tip: str | None = None,
) -> str:
    """Use Claude to improve the skill file based on failures.

    Args:
        skill_path: Path to skill directory or direct .md file
        failures: List of failed evaluation results
        passes: List of passing evaluation results (to preserve behavior)
        tip: Optional style tip for improvement

    Returns:
        New skill content
    """
    skill_file = get_skill_file(skill_path)
    current_skill = skill_file.read_text()

    # Load the tune-improve skill instructions
    tune_skill = _get_tune_improve_skill()

    # Summarize failures
    failure_summary = [summarize_failure_for_tuning(f) for f in failures]

    # Summarize passes (just prompt/expected, no need for full response)
    passes_section = ""
    if passes:
        pass_summary = [{"prompt": p["prompt"], "expected": p["expected"]} for p in passes]
        passes_section = f"""
## Passing Tests (DO NOT BREAK THESE)

The current SKILL.md correctly handles these - your changes MUST NOT break them:

{yaml.dump(pass_summary, default_flow_style=False)}
"""

    # Build prompt with skill instructions
    if tune_skill:
        prompt = f"""{tune_skill}

---

## Current SKILL.md

{current_skill}
{passes_section}
## Failures

These prompts did NOT produce the expected behavior:

{yaml.dump(failure_summary, default_flow_style=False)}

## Constraints

- Maximum lines: {MAX_SKILL_LINES}
{f"- Style tip: {tip}" if tip else ""}
"""
    else:
        # Fallback if skill file not found
        prompt = f"""Improve this SKILL.md so Claude exhibits the expected behavior.

## Current SKILL.md

{current_skill}
{passes_section}
## Failures

These prompts did NOT produce the expected behavior:

{yaml.dump(failure_summary, default_flow_style=False)}

## Your Task

Revise the SKILL.md to fix the failures while PRESERVING behavior for passing tests.

CRITICAL: Do not break what's working! The passing tests above represent behavior that
must continue to work after your changes.

Common issues to fix:
- Description not specific enough about WHEN to trigger
- Instructions not explicit enough (Claude defaults to asking permission)
- Missing "do NOT ask" or "IMMEDIATELY" language for automatic behaviors

IMPORTANT CONSTRAINTS:
- Keep the SKILL.md under {MAX_SKILL_LINES} lines total
- Be concise but complete - don't remove instructions that make passing tests work
- Add specific handling for failing cases without breaking passing ones
{f"- Style tip: {tip}" if tip else ""}

Return ONLY the improved SKILL.md content (no explanation, no code fences)."""

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    result = strip_markdown(result)

    # Hard limit: truncate to MAX_SKILL_LINES if still too long
    lines = result.split("\n")
    if len(lines) > MAX_SKILL_LINES:
        result = "\n".join(lines[:MAX_SKILL_LINES])

    return result
