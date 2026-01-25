"""Print candidates as a Rich table."""

from rich.table import Table

from skillet.cli import console
from skillet.generate.types import CandidateEval

from .get_confidence_color import get_confidence_color


def print_candidates_table(candidates: list[CandidateEval]) -> None:
    """Print candidates as a table."""
    console.print()
    if not candidates:
        console.print("[yellow]No candidates generated.[/yellow]")
        return

    table = Table(title=f"Generated Candidates ({len(candidates)})")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Source")
    table.add_column("Confidence")

    for c in candidates:
        color = get_confidence_color(c.confidence)
        table.add_row(
            c.name,
            c.category,
            c.source,
            f"[{color}]{c.confidence:.0%}[/{color}]",
        )

    console.print(table)
