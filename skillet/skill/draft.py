"""Draft a SKILL.md from evals."""

from pathlib import Path

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import strip_markdown
from skillet.prompts import load_prompt

DRAFT_PROMPT = Path(__file__).parent / "draft.txt"


async def draft_skill(
    name: str,
    evals: list[dict],
    extra_prompt: str | None = None,
) -> str:
    """Use Claude to draft a SKILL.md based on captured evals.

    Args:
        name: Skill name
        evals: List of eval dicts with prompt/expected fields
        extra_prompt: Additional instructions for generation

    Returns:
        Generated SKILL.md content
    """
    evals_summary = "\n\n".join(
        [
            f"## Eval {i + 1}\nPrompt: {g['prompt']}\nExpected: {g['expected']}"
            for i, g in enumerate(evals)
        ]
    )

    extra_section = ""
    if extra_prompt:
        extra_section = f"\n# Additional Instructions\n\n{extra_prompt}\n"

    prompt = load_prompt(
        DRAFT_PROMPT,
        name=name,
        evals_summary=evals_summary,
        extra_section=extra_section,
    )

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    return strip_markdown(result)
