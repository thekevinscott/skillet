"""CLI handler for tune command."""

from pathlib import Path

from rich.panel import Panel

from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.gaps import load_gaps
from skillet.tune import tune


async def tune_command(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
):
    """Run tune command with display."""
    gaps = load_gaps(name)

    # Print header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Tuning:[/bold] {name}\n"
            f"[bold]Skill:[/bold] [cyan]{skill_path}[/cyan]\n"
            f"[bold]Gaps:[/bold] {len(gaps)}\n"
            f"[bold]Target:[/bold] {target_pass_rate:.0f}% pass rate\n"
            f"[bold]Max rounds:[/bold] {max_rounds}",
            title="Skill Tuner",
        )
    )

    # Track display state
    display: LiveDisplay | None = None
    current_tasks: list[dict] = []

    async def on_round_start(round_num: int, total_rounds: int):
        nonlocal display, current_tasks
        console.print()
        console.rule(f"[bold]Round {round_num}/{total_rounds}[/bold]")
        console.print()
        # Reset for new round
        display = None
        current_tasks = []

    async def on_eval_status(task: dict, state: str, result: dict | None):
        nonlocal display, current_tasks
        if task not in current_tasks:
            current_tasks.append(task)

        if display is None and len(current_tasks) > 0:
            # Initialize display with tasks we've seen so far
            display = LiveDisplay(current_tasks)
            await display.start()

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
        # This is tricky with the Progress context manager
        # We'll just print the tip
        console.print(f"Improving SKILL.md [dim](tip: {tip[:40]}...)[/dim]")

    async def on_improved(_new_content: str):
        console.print("[green]Updated SKILL.md[/green]")

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
    if result["success"]:
        console.print("[bold green]✓ Target reached! Skill tuned successfully.[/bold green]")
    else:
        console.print(
            f"[bold red]✗ Did not reach {result['target']:.0f}% "
            f"after {result['rounds']} rounds.[/bold red]"
        )
        console.print(f"  Current pass rate: {result['pass_rate']:.0f}%")
        console.print("  Try running [bold]skillet tune[/bold] again or edit SKILL.md manually.")
