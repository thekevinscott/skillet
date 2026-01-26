"""CLI handler for generate-evals command."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from skillet.cli import console
from skillet.generate import generate_evals


async def generate_evals_command(
    skill_path: Path,
    *,
    output_dir: Path | None = None,
    max_per_category: int = 5,
    dry_run: bool = False,
) -> None:
    """Run generate-evals with progress spinner."""
    skill_path = Path(skill_path).expanduser().resolve()
    final_output = None if dry_run else output_dir

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Generating evals from {skill_path.name}...", total=None)
        result = await generate_evals(
            skill_path,
            output_dir=final_output,
            max_per_category=max_per_category,
        )

    # Display analysis summary
    analysis = result.analysis
    console.print()
    console.print("[bold]Skill Analysis:[/bold]")
    console.print(f"  Name: [cyan]{analysis.get('name', 'unnamed')}[/cyan]")
    console.print(f"  Goals: {len(analysis.get('goals', []))}")
    console.print(f"  Prohibitions: {len(analysis.get('prohibitions', []))}")
    console.print(f"  Examples: {analysis.get('example_count', 0)}")
    # Display candidates table
    console.print()
    if not result.candidates:
        console.print("[yellow]No candidates generated.[/yellow]")
    else:
        table = Table(title=f"Generated {len(result.candidates)} Candidates")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Source")
        for c in result.candidates:
            table.add_row(c.name, c.category, c.source)
        console.print(table)
