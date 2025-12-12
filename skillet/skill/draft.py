"""Draft a SKILL.md from gaps."""

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import strip_markdown


async def draft_skill(
    name: str,
    gaps: list[dict],
    extra_prompt: str | None = None,
) -> str:
    """Use Claude to draft a SKILL.md based on captured gaps.

    Args:
        name: Skill name
        gaps: List of gap dicts with prompt/expected fields
        extra_prompt: Additional instructions for generation

    Returns:
        Generated SKILL.md content
    """
    gaps_summary = "\n\n".join(
        [
            f"## Gap {i + 1}\nPrompt: {g['prompt']}\nExpected: {g['expected']}"
            for i, g in enumerate(gaps)
        ]
    )

    extra_section = ""
    if extra_prompt:
        extra_section = f"\n# Additional Instructions\n\n{extra_prompt}\n"

    prompt = f"""Draft a minimal SKILL.md to address these gaps.

# Gaps for "{name}"

{gaps_summary}
{extra_section}
# Requirements

- YAML frontmatter with `name` and `description` (description: what + when to trigger)
- Minimal instructions - just enough to pass the expected behavior
- No lengthy explanations or comprehensive documentation
- One or two short examples maximum

Return ONLY the SKILL.md content."""

    result = await query_assistant_text(prompt, max_turns=1, allowed_tools=[])
    return strip_markdown(result)
