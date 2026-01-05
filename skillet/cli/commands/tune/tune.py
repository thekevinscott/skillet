"""CLI handler for tune command."""

from pathlib import Path

from rich.panel import Panel

from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.evals import load_evals
from skillet.tune import TuneResult, tune
from skillet.tune.result import TuneCallbacks, TuneConfig

from ...display.thresholds import PASS_RATE_YELLOW, get_rate_color
from .output_path import get_default_output_path
from .print_result import print_tune_result


async def tune_command(  # noqa: C901 - complexity from inline display callbacks
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
        output_path = get_default_output_path(name)

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
                        "eval_idx": eval_idx,
                        "eval_source": eval_data["_source"],
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
        # Use green if target met, otherwise use threshold-based coloring
        if pass_rate >= target_pass_rate:
            rate_color = "green"
        else:
            rate_color = get_rate_color(pass_rate) if pass_rate >= PASS_RATE_YELLOW else "red"
        console.print(f"Pass rate: [{rate_color}]{pass_rate:.0f}%[/{rate_color}]")

        failures = [r for r in results if not r["pass"]]
        if failures:
            console.print(f"Failures: [red]{len(failures)}[/red]")
        console.print()

    async def on_improving(_tip: str):
        console.print("Improving skill...")

    async def on_improved(_new_content: str, _path: Path):
        console.print("[green]Skill improved[/green]")

    config = TuneConfig(
        max_rounds=max_rounds,
        target_pass_rate=target_pass_rate,
        samples=samples,
        parallel=parallel,
    )
    callbacks = TuneCallbacks(
        on_round_start=on_round_start,
        on_eval_status=on_eval_status,
        on_round_complete=on_round_complete,
        on_improving=on_improving,
        on_improved=on_improved,
    )

    result = await tune(
        name,
        skill_path,
        config=config,
        callbacks=callbacks,
    )

    print_tune_result(result)

    # Save results (always saves, either to provided path or default)
    result.save(output_path)
    console.print(f"\n[dim]Results saved to:[/dim] {output_path}")

    return result
