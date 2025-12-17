"""CLI handler for tune command."""

from datetime import datetime
from pathlib import Path

from rich.panel import Panel

from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.gaps import load_gaps
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
    gaps = load_gaps(name)

    # Default output path if not provided
    if output_path is None:
        output_path = _get_default_output_path(name)

    # Print header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Tuning:[/bold] {name}\n"
            f"[bold]Skill:[/bold] [cyan]{skill_path}[/cyan]\n"
            f"[bold]Evals:[/bold] {len(gaps)}\n"
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
        for gap_idx, gap in enumerate(gaps):
            for i in range(samples):
                tasks.append(
                    {
                        "gap_idx": gap_idx,
                        "gap_source": gap["_source"],
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
            display.finalize()

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

    async def on_improving(tip: str):
        console.print(f"Improving skill [dim](tip: {tip[:40]}...)[/dim]")

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

    console.print()
    if result.result.success:
        console.print("[bold green]✓ Target reached! Skill tuned successfully.[/bold green]")
    else:
        console.print(
            f"[bold red]✗ Did not reach {result.config.target_pass_rate:.0f}% "
            f"after {result.result.rounds_completed} rounds.[/bold red]"
        )
        console.print(f"  Current pass rate: {result.result.final_pass_rate:.0f}%")

    # Show best skill info
    console.print()
    console.print(f"[bold]Best round:[/bold] {result.result.best_round}")
    console.print(f"[bold]Best pass rate:[/bold] {result.result.final_pass_rate:.0f}%")

    # Save results (always saves, either to provided path or default)
    result.save(output_path)
    console.print(f"\n[dim]Results saved to:[/dim] {output_path}")

    return result
