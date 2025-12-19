"""CLI handler for tune command."""

from datetime import datetime
from pathlib import Path

from rich.panel import Panel

from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.gaps import load_evals
from skillet.tune import TuneResult, tune


def _get_default_output_path(name: str) -> Path:
    """Generate default output path for tune results.

    Returns ~/.skillet/tunes/{eval_name}/{timestamp}.json
    """
    # Extract eval name from path if it's a path
    eval_name = Path(name).name if "/" in name or "\\" in name else name

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    return Path.home() / ".skillet" / "tunes" / eval_name / f"{timestamp}.json"


async def tune_command(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
    output_path: Path | None = None,
) -> TuneResult:
    """Run tune command with display.

    Args:
        name: Name of eval set
        skill_path: Path to skill file
        max_rounds: Maximum tuning rounds
        target_pass_rate: Target pass rate percentage
        samples: Number of samples per eval
        parallel: Number of parallel workers
        output_path: Optional path to save results JSON (defaults to ~/.skillet/tunes/)

    Returns:
        TuneResult with all iterations
    """
    evals = load_evals(name)

    # Default output path if not provided
    if output_path is None:
        output_path = _get_default_output_path(name)

    # Print header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Tuning:[/bold] {name}\n"
            f"[bold]Skill:[/bold] [cyan]{skill_path}[/cyan]\n"
            f"[bold]Evals:[/bold] {len(evals)}\n"
            f"[bold]Target:[/bold] {target_pass_rate:.0f}% pass rate\n"
            f"[bold]Max rounds:[/bold] {max_rounds}",
            title="Skill Tuner",
        )
    )

    # Track display state
    display: LiveDisplay | None = None

    async def on_round_start(round_num: int, total_rounds: int):
        nonlocal display
        console.print()
        console.rule(f"[bold]Round {round_num}/{total_rounds}[/bold]")
        console.print()

        # Build full task list upfront for display
        tasks = []
        for eval_idx, eval_data in enumerate(evals):
            for i in range(samples):
                tasks.append(
                    {
                        "gap_idx": eval_idx,
                        "gap_source": eval_data["_source"],
                        "iteration": i + 1,
                    }
                )

        display = LiveDisplay(tasks)
        await display.start()

    async def on_eval_status(task: dict, state: str, result: dict | None):
        nonlocal display
        if display:
            await display.update(task, state, result)

    async def on_round_complete(_round_num: int, pass_rate: float, results: list[dict]):
        nonlocal display
        if display:
            await display.stop()

        console.print()
        if pass_rate >= target_pass_rate:
            rate_color = "green"
        elif pass_rate >= 50:
            rate_color = "yellow"
        else:
            rate_color = "red"
        console.print(f"Pass rate: [{rate_color}]{pass_rate:.0f}%[/{rate_color}]")

        failures = [r for r in results if not r["pass"]]
        if failures:
            console.print(f"Failures: [red]{len(failures)}[/red]")
        console.print()

    async def on_improving(_tip: str):
        console.print("Improving skill...")

    async def on_improved(_new_content: str):
        console.print("[green]Skill improved[/green]")

    result = await tune(
        name,
        skill_path,
        max_rounds=max_rounds,
        target_pass_rate=target_pass_rate,
        samples=samples,
        parallel=parallel,
        on_round_start=on_round_start,
        on_eval_status=on_eval_status,
        on_round_complete=on_round_complete,
        on_improving=on_improving,
        on_improved=on_improved,
    )

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

    # Save results (always saves, either to provided path or default)
    result.save(output_path)
    console.print(f"\n[dim]Results saved to:[/dim] {output_path}")

    return result
