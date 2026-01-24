"""Print output directory tree and next steps."""

from pathlib import Path

from rich.tree import Tree

from skillet.cli import console
from skillet.generate.types import CandidateEval


def print_output_summary(candidates: list[CandidateEval], output_dir: Path) -> None:
    """Print output directory tree and next steps.

    Args:
        candidates: List of candidate evals that were written
        output_dir: Directory where candidates were written
    """
    tree = Tree(f"[bold green]Generated[/bold green] [cyan]{output_dir}/[/cyan]")
    for c in candidates:
        tree.add(f"{c.name}.yaml [dim]({c.category})[/dim]")
    console.print(tree)

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Review candidates in [cyan]{output_dir}/[/cyan]")
    console.print("  2. Edit prompts/expected values as needed")
    console.print("  3. Remove _meta comments after review")
    console.print("  4. Move reviewed evals to your eval directory")
