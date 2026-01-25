"""Formatting utilities for generate-evals display."""

# Truncation lengths for dry-run display
PROMPT_TRUNCATE = 100
EXPECTED_TRUNCATE = 80


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if too long."""
    return f"{text[:max_len]}..." if len(text) > max_len else text


def format_prompt(prompt: str | list[str]) -> str:
    """Format prompt for display, handling multi-turn prompts."""
    if isinstance(prompt, list):
        return " | ".join(prompt)
    return prompt
