"""Print available lint rules."""

from skillet.cli import console
from skillet.lint import ALL_RULES


def print_rules() -> None:
    """Print available lint rules to console."""
    console.print("[bold]Available lint rules:[/bold]\n")
    for rule in ALL_RULES:
        console.print(f"  [cyan]{rule.rule_id}[/cyan]")
        console.print(f"    {rule.description}\n")
