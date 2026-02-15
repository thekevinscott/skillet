"""Format prompts for the LLM judge."""


def format_prompt(prompt: str | list[str]) -> str:
    """Format prompt(s) for the judge, handling multi-turn conversations."""
    if isinstance(prompt, str):
        return prompt

    # Multi-turn: format as numbered conversation
    lines = []
    for i, p in enumerate(prompt, 1):
        lines.append(f"Turn {i}: {p}")
    return "\n".join(lines)
