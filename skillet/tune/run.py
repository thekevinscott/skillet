"""Run tuning iterations."""

import asyncio
import random
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet.errors import SkillError
from skillet.eval import judge_response, run_prompt
from skillet.evals import load_evals

from .improve import TUNE_TIPS, get_skill_file, improve_skill
from .result import RoundResult, TuneConfig, TuneResult
from .results_to_eval_results import results_to_eval_results


async def run_tune_eval(
    evals: list[dict],
    skill_path: Path,
    samples: int = 1,
    parallel: int = 3,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
) -> tuple[float, list[dict]]:
    """Run evals for tuning (no caching) and return pass rate + results."""
    tasks = []
    for eval_idx, eval_item in enumerate(evals):
        for i in range(samples):
            tasks.append(
                {
                    "eval_idx": eval_idx,
                    "eval_source": eval_item["_source"],
                    "eval_content": eval_item["_content"],
                    "iteration": i + 1,
                    "prompt": eval_item["prompt"],
                    "expected": eval_item["expected"],
                }
            )

    semaphore = asyncio.Semaphore(parallel)

    async def run_single(task):
        async with semaphore:
            if on_status:
                await on_status(task, "running", None)
            try:
                query_result = await run_prompt(task["prompt"], skill_path)
                judgment = await judge_response(
                    prompt=task["prompt"],
                    response=query_result.text,
                    expected=task["expected"],
                    tool_calls=query_result.tool_calls,
                )
                result = {
                    "eval_idx": task["eval_idx"],
                    "eval_source": task["eval_source"],
                    "iteration": task["iteration"],
                    "prompt": task["prompt"],
                    "expected": task["expected"],
                    "response": query_result.text,
                    "tool_calls": query_result.tool_calls,
                    "judgment": judgment,
                    "pass": judgment["pass"],
                }
                if on_status:
                    await on_status(task, "done", result)
                return result
            except Exception as e:
                result = {
                    "eval_idx": task["eval_idx"],
                    "eval_source": task["eval_source"],
                    "iteration": task["iteration"],
                    "prompt": task["prompt"],
                    "expected": task["expected"],
                    "response": str(e),
                    "tool_calls": [],
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


async def tune(  # noqa: PLR0913 - many args due to optional progress callbacks
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
) -> TuneResult:
    """Iteratively tune a skill until evals pass.

    The original skill file is NOT modified. Tuning happens in a temporary
    directory, and all iterations are tracked in the returned TuneResult.

    Args:
        name: Name of eval set
        skill_path: Path to skill file or directory
        max_rounds: Maximum tuning rounds
        target_pass_rate: Target pass rate percentage
        samples: Number of samples per eval
        parallel: Number of parallel workers
        on_round_start: Callback when round starts (round_num, max_rounds)
        on_eval_status: Callback for eval status updates
        on_round_complete: Callback when round completes (round_num, pass_rate, results)
        on_improving: Callback when starting improvement (tip)
        on_improved: Callback when improvement done (new_content)

    Returns:
        TuneResult with all iterations and the best skill content
    """
    evals = load_evals(name)

    # Read original skill content
    original_skill_file = get_skill_file(skill_path)
    original_skill_content = original_skill_file.read_text()

    # Create TuneResult to track everything
    tune_result = TuneResult.create(
        eval_set=name,
        skill_path=skill_path,
        original_skill=original_skill_content,
        config=TuneConfig(
            max_rounds=max_rounds,
            target_pass_rate=target_pass_rate,
            samples=samples,
            parallel=parallel,
        ),
    )

    # Create temporary directory that mirrors the skill's location
    # This is needed because Claude loads skills from .claude/commands/
    with tempfile.TemporaryDirectory(prefix="skillet-tune-") as temp_dir:
        # Copy the skill file to temp location, preserving directory structure
        # e.g., .claude/commands/skillet/add.md -> /tmp/xxx/.claude/commands/skillet/add.md
        if ".claude" in skill_path.parts:
            claude_idx = skill_path.parts.index(".claude")
            relative_path = Path(*skill_path.parts[claude_idx:])
            temp_skill_path = Path(temp_dir) / relative_path
        else:
            # Simple case: just use the filename
            temp_skill_path = Path(temp_dir) / original_skill_file.name

        try:
            temp_skill_path.parent.mkdir(parents=True, exist_ok=True)
            temp_skill_path.write_text(original_skill_content)
        except OSError as e:
            raise SkillError(f"Failed to write temp skill file: {e}") from e

        current_skill_content = original_skill_content
        last_tip: str | None = None  # Track tip from previous round

        for round_num in range(1, max_rounds + 1):
            if on_round_start:
                await on_round_start(round_num, max_rounds)

            # Run evals using temp skill path
            pass_rate, results = await run_tune_eval(
                evals, temp_skill_path, samples, parallel, on_eval_status
            )

            # Create round result (tip_used is from previous iteration)
            round_result = RoundResult(
                round=round_num,
                pass_rate=pass_rate,
                skill_content=current_skill_content,
                tip_used=last_tip,
                evals=results_to_eval_results(results),
            )
            tune_result.add_round(round_result)

            if on_round_complete:
                await on_round_complete(round_num, pass_rate, results)

            if pass_rate >= target_pass_rate:
                tune_result.finalize(success=True)
                return tune_result

            # Get failures and improve
            failures = [r for r in results if not r["pass"]]
            last_tip = random.choice(TUNE_TIPS)

            if on_improving:
                await on_improving(last_tip)

            # Improve skill (reads from temp path)
            new_content = await improve_skill(temp_skill_path, failures, last_tip)
            current_skill_content = new_content

            # Write improved version to temp file
            try:
                temp_skill_path.write_text(new_content + "\n")
            except OSError as e:
                raise SkillError(f"Failed to write improved skill: {e}") from e

            if on_improved:
                await on_improved(new_content)

        tune_result.finalize(success=False)
        return tune_result
