"""CLI handler for eval command."""

import logging
from pathlib import Path

from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.eval import evaluate

from ...display.thresholds import get_rate_color
from .get_scripts_from_evals import get_scripts_from_evals
from .prompt_for_script_confirmation import prompt_for_script_confirmation
from .summarize import summarize_responses

logger = logging.getLogger(__name__)


async def eval_command(
    name: str,
    skill_path: Path | None = None,
    samples: int = 3,
    max_evals: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
    skip_cache: bool = False,
    trust: bool = False,
):
    """Run eval command with display."""
    from skillet.evals import load_evals

    # Print header
    console.print()
    if skill_path:
        console.print("[bold]Eval Results (with skill)[/bold]")
        console.print(f"Skill: [cyan]{skill_path}[/cyan]")
    else:
        console.print("[bold]Eval Results (baseline, no skill)[/bold]")

    # Load evals first to build the task list for display
    evals = load_evals(name)
    if max_evals and max_evals < len(evals):
        import random

        evals = random.sample(evals, max_evals)

    # Check for scripts and prompt if needed
    scripts = get_scripts_from_evals(evals)
    if scripts and not trust and not prompt_for_script_confirmation(scripts):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Build task list for display initialization
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

    # Create and start live display
    display = LiveDisplay(tasks)
    await display.start()

    async def on_status(task: dict, state: str, result: dict | None):
        await display.update(task, state, result)

    try:
        # Run the evaluation with live updates
        eval_result = await evaluate(
            name,
            skill_path=skill_path,
            samples=samples,
            max_evals=max_evals,
            allowed_tools=allowed_tools,
            parallel=parallel,
            on_status=on_status,
            skip_cache=skip_cache,
        )
    finally:
        await display.stop()

    # Print results info
    if max_evals and eval_result["sampled_evals"] < eval_result["total_evals"]:
        console.print(
            f"Evals: {eval_result['sampled_evals']} "
            f"[dim](sampled from {eval_result['total_evals']})[/dim]"
        )
    else:
        console.print(f"Evals: {eval_result['sampled_evals']}")
    console.print(f"Samples: {samples} per eval")
    console.print(f"Parallel: {parallel}")
    console.print(f"Tools: {', '.join(allowed_tools) if allowed_tools else 'all'}")
    console.print(f"Total runs: {eval_result['total_runs']}")
    console.print()

    # Show final status
    display.finalize()

    # Stats
    console.print()
    if eval_result["cached_count"] > 0:
        console.print(
            f"Cache: [blue]{eval_result['cached_count']} cached[/blue], "
            f"{eval_result['fresh_count']} fresh"
        )

    rate_color = get_rate_color(eval_result["pass_rate"])
    console.print(
        f"Overall pass rate: [{rate_color}]{eval_result['pass_rate']:.0f}%[/{rate_color}] "
        f"({eval_result['total_pass']}/{eval_result['total_runs']})"
    )

    # Generate summary of failures if any
    failures = [r for r in eval_result["results"] if not r["pass"]]
    if failures and eval_result["fresh_count"] > 0:
        console.print()
        console.print("[bold]What Claude did instead:[/bold]")
        summary = await summarize_responses(failures)
        console.print(summary)
