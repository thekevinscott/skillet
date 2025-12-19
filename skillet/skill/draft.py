"""Draft a SKILL.md from evals."""

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import strip_markdown


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

    prompt = f"""Draft a minimal SKILL.md to address these evals.

# Evals for "{name}"

{evals_summary}
{extra_section}
# Requirements

- YAML frontmatter with `name` and `description` (description: what + when to trigger)
- Minimal instructions - just enough to pass the expected behavior
- No lengthy explanations or comprehensive documentation
- One or two short examples maximum

Return ONLY the SKILL.md content."""

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    return strip_markdown(result)
