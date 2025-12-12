"""Run tuning iterations."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet.eval.judge import judge_response
from skillet.eval.run import run_prompt
from skillet.gaps import load_gaps

from .improve import TUNE_TIPS, improve_skill


async def run_tune_eval(
    gaps: list[dict],
    skill_path: Path,
    samples: int = 1,
    parallel: int = 3,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
) -> tuple[float, list[dict]]:
    """Run evals for tuning (no caching) and return pass rate + results."""
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

    semaphore = asyncio.Semaphore(parallel)

    async def run_single(task):
        async with semaphore:
            if on_status:
                await on_status(task, "running", None)
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
                if on_status:
                    await on_status(task, "done", result)
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
                if on_status:
                    await on_status(task, "done", result)
                return result

    results = await asyncio.gather(*[run_single(t) for t in tasks])

    total_pass = sum(1 for r in results if r["pass"])
    pass_rate = total_pass / len(results) * 100 if results else 0

    return pass_rate, list(results)


async def tune(
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
    on_round_start: Callable[[int, int], Awaitable[None]] | None = None,
    on_eval_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
    on_round_complete: Callable[[int, float, list[dict]], Awaitable[None]] | None = None,
    on_improving: Callable[[str], Awaitable[None]] | None = None,
    on_improved: Callable[[str], Awaitable[None]] | None = None,
) -> dict:
    """Iteratively tune a skill until evals pass.

    Args:
        name: Name of gap set
        skill_path: Path to skill directory
        max_rounds: Maximum tuning rounds
        target_pass_rate: Target pass rate percentage
        samples: Number of eval samples per gap
        parallel: Number of parallel workers
        on_round_start: Callback when round starts (round_num, max_rounds)
        on_eval_status: Callback for eval status updates
        on_round_complete: Callback when round completes (round_num, pass_rate, results)
        on_improving: Callback when starting improvement (tip)
        on_improved: Callback when improvement done (new_content)

    Returns:
        dict with success status, final pass_rate, rounds completed
    """
    gaps = load_gaps(name)

    final_pass_rate = 0.0
    for round_num in range(1, max_rounds + 1):
        if on_round_start:
            await on_round_start(round_num, max_rounds)

        # Run evals
        pass_rate, results = await run_tune_eval(
            gaps, skill_path, samples, parallel, on_eval_status
        )
        final_pass_rate = pass_rate

        if on_round_complete:
            await on_round_complete(round_num, pass_rate, results)

        if pass_rate >= target_pass_rate:
            return {
                "success": True,
                "pass_rate": pass_rate,
                "rounds": round_num,
                "target": target_pass_rate,
            }

        # Get failures and improve
        failures = [r for r in results if not r["pass"]]
        tip = random.choice(TUNE_TIPS)

        if on_improving:
            await on_improving(tip)

        new_content = await improve_skill(skill_path, failures, tip)

        # Write new version
        skill_file = skill_path / "SKILL.md"
        skill_file.write_text(new_content + "\n")

        if on_improved:
            await on_improved(new_content)

    return {
        "success": False,
        "pass_rate": final_pass_rate,
        "rounds": max_rounds,
        "target": target_pass_rate,
    }
