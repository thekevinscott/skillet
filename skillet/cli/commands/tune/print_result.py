"""Print tune result summary."""

from skillet.cli import console
from skillet.tune import TuneResult


def print_tune_result(result: TuneResult) -> None:
    """Print the final tune result summary."""
    console.print()

    # Handle edge case of no rounds (e.g., early termination)
    if not result.rounds:
        console.print("[bold yellow]→ No rounds completed[/bold yellow]")
        console.print(f"[dim]Completed {result.result.rounds_completed} rounds[/dim]")
        return

    # Compare against baseline (round 1)
    baseline = result.rounds[0].pass_rate
    best = result.result.final_pass_rate
    delta = best - baseline

    if delta > 0:
        console.print(
            f"[bold green]✓ Improved over baseline: "
            f"{baseline:.0f}% → {best:.0f}% (+{delta:.0f}%)[/bold green]"
        )
    else:
        # delta == 0: best stayed at baseline (round 1)
        # Note: delta < 0 is impossible since TuneResult.add_round only updates
        # final_pass_rate when the new round's rate is >= current best
        console.print(
            f"[bold yellow]→ No improvement: {baseline:.0f}% (best was round 1)[/bold yellow]"
        )

    console.print(f"[dim]Completed {result.result.rounds_completed} rounds[/dim]")
