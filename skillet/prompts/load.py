"""Prompt template loading utilities."""

from pathlib import Path
from string import Template


def load_prompt(prompt_path: str | Path, **variables: str) -> str:
    """Load a prompt template and substitute variables.

    Uses ${var} syntax for substitution.

    Args:
        prompt_path: Path to the .txt prompt file
        **variables: Key-value pairs to substitute in the template

    Returns:
        The prompt with all variables substituted

    Raises:
        KeyError: If a required variable is missing
        FileNotFoundError: If the prompt file doesn't exist

    Example:
        prompt = load_prompt("skillet/eval/judge.txt", response=response)
    """
    path = Path(prompt_path)
    template = Template(path.read_text())
    return template.substitute(variables)
