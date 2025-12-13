"""CLI handler for compare command."""

from pathlib import Path

from rich.table import Table

from skillet.cli import console
from skillet.compare import compare


def format_delta(baseline: float | None, skill: float | None) -> str:
    """Format delta with color."""
    if baseline is None or skill is None:
        return "-"
    delta = skill - baseline
    if delta > 0:
        return f"[green]+{delta:.0f}%[/green]"
    elif delta < 0:
        return f"[red]{delta:.0f}%[/red]"
    else:
        return "0%"


def compare_command(name: str, skill_path: Path):
    """Run compare command with display."""
    result = compare(name, skill_path)

    # Check for missing data
    if result["missing_baseline"]:
        console.print(
            f"[yellow]Warning:[/yellow] No baseline cache for: "
            f"{', '.join(result['missing_baseline'])}"
        )
        console.print(f"Run: [bold]skillet eval {name}[/bold]")
        console.print()

    if result["missing_skill"]:
        console.print(
            f"[yellow]Warning:[/yellow] No skill cache for: {', '.join(result['missing_skill'])}"
        )
        console.print(f"Run: [bold]skillet eval {name} {skill_path}[/bold]")
        console.print()

    # Build comparison table
    table = Table(title=f"Comparison: {name}")
    table.add_column("Gap", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("Skill", justify="right")
    table.add_column("Δ", justify="right")

    # Per-gap results
    for r in result["results"]:
        baseline_str = f"{r['baseline']:.0f}%" if r["baseline"] is not None else "-"
        skill_str = f"{r['skill']:.0f}%" if r["skill"] is not None else "-"
        delta_str = format_delta(r["baseline"], r["skill"])

        table.add_row(r["source"], baseline_str, skill_str, delta_str)

    # Overall row
    baseline_str = (
        f"{result['overall_baseline']:.0f}%" if result["overall_baseline"] is not None else "-"
    )
    skill_str = f"{result['overall_skill']:.0f}%" if result["overall_skill"] is not None else "-"
    delta_str = format_delta(result["overall_baseline"], result["overall_skill"])

    table.add_section()
    table.add_row("[bold]Overall[/bold]", baseline_str, skill_str, delta_str)

    console.print(table)
