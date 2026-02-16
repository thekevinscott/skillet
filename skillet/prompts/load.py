"""Prompt template loading utilities."""

from pathlib import Path
from string import Template


def load_prompt(prompt_path: str | Path, **variables: str) -> str:
    """Load a prompt template and substitute variables.

    Uses ${var} syntax for substitution. Unrecognized $-patterns (e.g.
    $HOME in eval content) pass through unchanged rather than raising.
    """
    path = Path(prompt_path)
    template = Template(path.read_text())
    return template.safe_substitute(variables)
