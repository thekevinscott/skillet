"""CLI handler for eval command."""

from pathlib import Path

import yaml

from skillet._internal.sdk import query_assistant_text
from skillet._internal.text import summarize_failure_for_eval
from skillet.cli import console
from skillet.cli.display import LiveDisplay
from skillet.eval import evaluate


async def summarize_responses(results: list[dict]) -> str:
    """Summarize what Claude actually did across failed responses."""
    response_summaries = [summarize_failure_for_eval(r) for r in results]

    responses_yaml = yaml.dump(response_summaries, default_flow_style=False)
    summary_prompt = f"""Analyze these AI responses that failed to meet expectations.
Summarize the PATTERNS in what the AI did instead.

## Failed Responses

{responses_yaml}

## Your Task

Write 2-4 bullet points summarizing what the AI typically did instead of expected.
Be specific and concise. Format as: - Pattern description (X% of responses)

Focus on the FORMAT or BEHAVIOR patterns, not the content quality.
"""

    return await query_assistant_text(summary_prompt, max_turns=1, allowed_tools=[])


async def eval_command(
    name: str,
    skill_path: Path | None = None,
    samples: int = 3,
    max_gaps: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
):
    """Run eval command with display."""
    # Print header
    console.print()
    if skill_path:
        console.print("[bold]Eval Results (with skill)[/bold]")
        console.print(f"Skill: [cyan]{skill_path}[/cyan]")
    else:
        console.print("[bold]Eval Results (baseline, no skill)[/bold]")

    # We need to create the display before running, but we need tasks first
    # So we do a preliminary setup here - a bit awkward but keeps API clean

    # Create a wrapper to track tasks and display
    display: LiveDisplay | None = None
    tasks_ref: list[dict] = []

    async def on_status(task: dict, state: str, result: dict | None):
        nonlocal display, tasks_ref
        # Initialize display on first task
        if display is None:
            # We need the full task list - get it from the eval module
            # This is called with each task, so we build incrementally
            if task not in tasks_ref:
                tasks_ref.append(task)
        else:
            await display.update(task, state, result)

    # Run the evaluation
    eval_result = await evaluate(
        name,
        skill_path=skill_path,
        samples=samples,
        max_gaps=max_gaps,
        allowed_tools=allowed_tools,
        parallel=parallel,
    )

    # Now create and run display with full task list
    display = LiveDisplay(eval_result["tasks"])
    for task in eval_result["tasks"]:
        # Find matching result
        for r in eval_result["results"]:
            if r["gap_idx"] == task["gap_idx"] and r["iteration"] == task["iteration"]:
                state = "cached" if r.get("cached") else "done"
                await display.update(task, state, r)
                break

    # Print results info
    if max_gaps and eval_result["sampled_gaps"] < eval_result["total_gaps"]:
        console.print(
            f"Gaps: {eval_result['sampled_gaps']} "
            f"[dim](sampled from {eval_result['total_gaps']})[/dim]"
        )
    else:
        console.print(f"Gaps: {eval_result['sampled_gaps']}")
    console.print(f"Samples: {samples} per gap")
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

    rate_color = (
        "green"
        if eval_result["pass_rate"] >= 80
        else "yellow"
        if eval_result["pass_rate"] >= 50
        else "red"
    )
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
