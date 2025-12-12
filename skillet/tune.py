"""Iteratively tune a skill until evals pass."""

import asyncio
import random
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from skillet.eval import LiveDisplay, load_gaps, run_prompt
from skillet.judge import judge_response

console = Console()

# Tips to explore instruction space (inspired by DSPy MIPROv2)
TUNE_TIPS = [
    "Be extremely terse - every word must earn its place",
    "Use imperatives: DO this, NEVER do that",
    "Focus on the trigger condition - when exactly should this activate?",
    "Emphasize what NOT to do - Claude defaults to asking permission",
    "Use bullet points, not paragraphs",
    "Put the most important instruction first",
    "Add a concrete example of correct behavior",
    "Make the description more specific about when to trigger",
    "Use CAPS for critical words like IMMEDIATELY, NEVER, MUST",
]


async def run_eval_for_tune(
    gaps: list[dict],
    skill_path: Path,
    samples: int = 1,
    parallel: int = 3,
) -> tuple[float, list[dict]]:
    """Run evals and return pass rate + results."""

    tasks = []
    for gap_idx, gap in enumerate(gaps):
        for i in range(samples):
            tasks.append(
                {
                    "gap_idx": gap_idx,
                    "gap_source": gap["_source"],
                    "gap_content": gap["_content"],
                    "iteration": i + 1,
                    "prompt": gap["prompt"],
                    "expected": gap["expected"],
                }
            )

    display = LiveDisplay(tasks)
    semaphore = asyncio.Semaphore(parallel)

    async def run_single(task):
        async with semaphore:
            await display.update(task, "running")
            try:
                response = await run_prompt(task["prompt"], skill_path)
                judgment = await judge_response(
                    prompt=task["prompt"],
                    response=response,
                    expected=task["expected"],
                )
                result = {
                    "gap_idx": task["gap_idx"],
                    "gap_source": task["gap_source"],
                    "iteration": task["iteration"],
                    "prompt": task["prompt"],
                    "expected": task["expected"],
                    "response": response,
                    "judgment": judgment,
                    "pass": judgment["pass"],
                }
                await display.update(task, "done", result)
                return result
            except Exception as e:
                result = {
                    "gap_idx": task["gap_idx"],
                    "gap_source": task["gap_source"],
                    "iteration": task["iteration"],
                    "prompt": task["prompt"],
                    "expected": task["expected"],
                    "response": str(e),
                    "judgment": {"pass": False, "reasoning": f"Error: {e}"},
                    "pass": False,
                }
                await display.update(task, "done", result)
                return result

    await display.start()
    results = await asyncio.gather(*[run_single(t) for t in tasks])
    await display.stop()
    display.finalize()

    total_pass = sum(1 for r in results if r["pass"])
    pass_rate = total_pass / len(results) * 100 if results else 0

    return pass_rate, results


async def improve_skill(
    skill_path: Path,
    failures: list[dict],
    tip: str | None = None,
) -> str:
    """Use Claude to improve the SKILL.md based on failures."""
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    current_skill = (skill_path / "SKILL.md").read_text()

    # Summarize failures
    failure_summary = []
    for f in failures:
        failure_summary.append(
            {
                "prompt": f["prompt"],
                "expected": f["expected"],
                "actual_response": f["response"][:500] if f.get("response") else "",
                "why_failed": f["judgment"].get("reasoning", ""),
            }
        )

    prompt = f"""Improve this SKILL.md so Claude exhibits the expected behavior.

## Current SKILL.md

{current_skill}

## Failures

These prompts did NOT produce the expected behavior:

{yaml.dump(failure_summary, default_flow_style=False)}

## Your Task

Revise the SKILL.md to fix these failures. Common issues:
- Description not specific enough about WHEN to trigger
- Instructions not explicit enough (Claude defaults to asking permission)
- Missing "do NOT ask" or "IMMEDIATELY" language for automatic behaviors

IMPORTANT CONSTRAINTS:
- Keep the SKILL.md under 50 lines total
- Be concise - shorter is better
- Replace verbose instructions with terse, direct ones
- Do NOT keep adding more text - rewrite to be minimal
{f"- Style tip: {tip}" if tip else ""}

Return ONLY the improved SKILL.md content (no explanation, no code fences)."""

    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
    )

    result = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text

    result = result.strip()

    # Strip markdown code fences if present
    if result.startswith("```markdown"):
        result = result[len("```markdown") :].strip()
    if result.startswith("```"):
        result = result[3:].strip()
    if result.endswith("```"):
        result = result[:-3].strip()

    # Hard limit: truncate to 50 lines if still too long
    lines = result.split("\n")
    if len(lines) > 50:
        result = "\n".join(lines[:50])

    return result


async def tune(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
):
    """Iteratively tune a skill until evals pass."""

    gaps = load_gaps(name)

    # Print header
    console.print()
    console.print(Panel.fit(
        f"[bold]Tuning:[/bold] {name}\n"
        f"[bold]Skill:[/bold] [cyan]{skill_path}[/cyan]\n"
        f"[bold]Gaps:[/bold] {len(gaps)}\n"
        f"[bold]Target:[/bold] {target_pass_rate:.0f}% pass rate\n"
        f"[bold]Max rounds:[/bold] {max_rounds}",
        title="Skill Tuner",
    ))

    for round_num in range(1, max_rounds + 1):
        console.print()
        console.rule(f"[bold]Round {round_num}/{max_rounds}[/bold]")
        console.print()

        # Run evals
        pass_rate, results = await run_eval_for_tune(gaps, skill_path, samples, parallel)

        console.print()
        if pass_rate >= target_pass_rate:
            rate_color = "green"
        elif pass_rate >= 50:
            rate_color = "yellow"
        else:
            rate_color = "red"
        console.print(f"Pass rate: [{rate_color}]{pass_rate:.0f}%[/{rate_color}]")

        if pass_rate >= target_pass_rate:
            console.print()
            console.print("[bold green]✓ Target reached! Skill tuned successfully.[/bold green]")
            return

        # Get failures
        failures = [r for r in results if not r["pass"]]
        console.print(f"Failures: [red]{len(failures)}[/red]")
        console.print()

        # Improve skill with a random tip
        tip = random.choice(TUNE_TIPS)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Improving SKILL.md [dim](tip: {tip[:30]}...)[/dim]", total=None)
            new_content = await improve_skill(skill_path, failures, tip)

        # Write new version
        skill_file = skill_path / "SKILL.md"
        skill_file.write_text(new_content + "\n")
        console.print("[green]Updated SKILL.md[/green]")

    # Didn't reach target
    console.print()
    console.print(
        f"[bold red]✗ Did not reach {target_pass_rate:.0f}% "
        f"after {max_rounds} rounds.[/bold red]"
    )
    console.print(f"  Current pass rate: {pass_rate:.0f}%")
    console.print("  Try running [bold]skillet tune[/bold] again or edit SKILL.md manually.")
