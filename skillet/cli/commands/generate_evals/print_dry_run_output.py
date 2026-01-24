"""Print dry-run candidate details."""

from skillet.cli import console
from skillet.generate.types import CandidateEval

from .format_utils import EXPECTED_TRUNCATE, PROMPT_TRUNCATE, format_prompt, truncate


def print_dry_run_output(candidates: list[CandidateEval]) -> None:
    """Print dry-run candidate details.

    Args:
        candidates: List of candidate evals to display
    """
    console.print()
    console.print("[dim]Dry run - no files written.[/dim]")
    console.print()
    console.print("[bold]Candidate prompts:[/bold]")
    for c in candidates:
        console.print(f"\n[cyan]{c.name}[/cyan] ({c.category})")
        prompt_str = format_prompt(c.prompt)
        console.print(f"  Prompt: {truncate(prompt_str, PROMPT_TRUNCATE)}")
        console.print(f"  Expected: {truncate(c.expected, EXPECTED_TRUNCATE)}")
