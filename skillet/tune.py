"""Iteratively tune a skill until evals pass."""

import asyncio
import random
from pathlib import Path

import click
import yaml

from skillet.cache import gap_cache_key, get_cache_dir, save_iteration, hash_directory
from skillet.eval import load_gaps, run_prompt_async, LiveDisplay
from skillet.judge import judge_response_async


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
    name: str,
    gaps: list[dict],
    skill_path: Path,
    samples: int = 1,
    parallel: int = 3,
) -> tuple[float, list[dict]]:
    """Run evals and return pass rate + results."""

    tasks = []
    for gap_idx, gap in enumerate(gaps):
        for i in range(samples):
            tasks.append({
                "gap_idx": gap_idx,
                "gap_source": gap["_source"],
                "gap_content": gap["_content"],
                "iteration": i + 1,
                "prompt": gap["prompt"],
                "expected": gap["expected"],
            })

    display = LiveDisplay(tasks)
    semaphore = asyncio.Semaphore(parallel)

    async def run_single(task):
        async with semaphore:
            await display.update(task, "running")
            try:
                response = await run_prompt_async(task["prompt"], skill_path)
                judgment = await judge_response_async(
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


async def improve_skill_async(
    skill_path: Path,
    gaps: list[dict],
    failures: list[dict],
    tip: str | None = None,
) -> str:
    """Use Claude to improve the SKILL.md based on failures."""
    from claude_agent_sdk import query, AssistantMessage, TextBlock, ClaudeAgentOptions

    current_skill = (skill_path / "SKILL.md").read_text()

    # Summarize failures
    failure_summary = []
    for f in failures:
        failure_summary.append({
            "prompt": f["prompt"],
            "expected": f["expected"],
            "actual_response": f["response"][:500] if f.get("response") else "",
            "why_failed": f["judgment"].get("reasoning", ""),
        })

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
        result = result[len("```markdown"):].strip()
    if result.startswith("```"):
        result = result[3:].strip()
    if result.endswith("```"):
        result = result[:-3].strip()

    # Hard limit: truncate to 50 lines if still too long
    lines = result.split("\n")
    if len(lines) > 50:
        result = "\n".join(lines[:50])

    return result


async def tune_async(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
):
    """Iteratively tune a skill until evals pass."""

    gaps = load_gaps(name)

    click.echo(f"\nTuning: {name}")
    click.echo(f"Skill: {skill_path}")
    click.echo(f"Gaps: {len(gaps)}")
    click.echo(f"Target: {target_pass_rate:.0f}% pass rate")
    click.echo(f"Max rounds: {max_rounds}")
    click.echo()

    for round_num in range(1, max_rounds + 1):
        click.echo(f"── Round {round_num}/{max_rounds} ──")
        click.echo()

        # Run evals
        pass_rate, results = await run_eval_for_tune(
            name, gaps, skill_path, samples, parallel
        )

        click.echo()
        click.echo(f"Pass rate: {pass_rate:.0f}%")

        if pass_rate >= target_pass_rate:
            click.echo()
            click.echo(f"✓ Target reached! Skill tuned successfully.")
            return

        # Get failures
        failures = [r for r in results if not r["pass"]]
        click.echo(f"Failures: {len(failures)}")
        click.echo()

        # Improve skill with a random tip
        tip = random.choice(TUNE_TIPS)
        click.echo(f"Improving SKILL.md (tip: {tip[:40]}...)")
        new_content = await improve_skill_async(skill_path, gaps, failures, tip)

        # Write new version
        skill_file = skill_path / "SKILL.md"
        skill_file.write_text(new_content + "\n")
        click.echo("Updated SKILL.md")
        click.echo()

    # Didn't reach target
    click.echo(f"✗ Did not reach {target_pass_rate:.0f}% after {max_rounds} rounds.")
    click.echo(f"  Current pass rate: {pass_rate:.0f}%")
    click.echo(f"  Try running `skillet tune` again or edit SKILL.md manually.")


def run_tune(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
):
    """Sync wrapper for tune_async."""
    try:
        asyncio.run(tune_async(
            name, skill_path, max_rounds, target_pass_rate, samples, parallel
        ))
    except KeyboardInterrupt:
        click.echo("\n\nAborted.")
        raise SystemExit(0)
