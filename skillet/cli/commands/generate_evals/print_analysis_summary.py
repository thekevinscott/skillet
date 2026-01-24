"""Print skill analysis summary."""

from skillet.cli import console


def print_analysis_summary(analysis: dict) -> None:
    """Print skill analysis summary.

    Args:
        analysis: Dict containing name, goals, prohibitions, example_count
    """
    console.print()
    console.print("[bold]Skill Analysis:[/bold]")
    console.print(f"  Name: [cyan]{analysis.get('name', 'unnamed')}[/cyan]")
    console.print(f"  Goals: {len(analysis.get('goals', []))}")
    console.print(f"  Prohibitions: {len(analysis.get('prohibitions', []))}")
    console.print(f"  Examples: {analysis.get('example_count', 0)}")
