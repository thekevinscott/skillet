"""Print tune result summary."""

from skillet.cli import console
from skillet.tune import TuneResult


def print_tune_result(result: TuneResult) -> None:
    """Print the final tune result summary."""
    # Compare against baseline (round 1)
    console.print()
    baseline = result.rounds[0].pass_rate if result.rounds else 0
    best = result.result.final_pass_rate
    delta = best - baseline

    if delta > 0:
        console.print(
            f"[bold green]✓ Improved over baseline: "
            f"{baseline:.0f}% → {best:.0f}% (+{delta:.0f}%)[/bold green]"
        )
    elif delta == 0:
        console.print(
            f"[bold yellow]→ No improvement: {baseline:.0f}% (best was round 1)[/bold yellow]"
        )
    else:
        console.print(
            f"[bold yellow]→ Best was baseline: {baseline:.0f}% "
            f"(round {result.result.best_round})[/bold yellow]"
        )

    console.print(f"[dim]Completed {result.result.rounds_completed} rounds[/dim]")
