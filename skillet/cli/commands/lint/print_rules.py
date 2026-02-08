"""Print available lint rules."""

from skillet.cli import console
from skillet.lint.rules import ALL_RULES


def print_rules() -> None:
    """Print all registered lint rules."""
    for rule in ALL_RULES:
        console.print(f"[cyan]{rule.name}[/cyan]: {rule.description}")
