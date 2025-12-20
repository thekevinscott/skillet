"""Run evaluations against evals."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet._internal.cache import (
    eval_cache_key,
    get_cache_dir,
    get_cached_iterations,
    save_iteration,
)
from skillet._internal.lock import cache_lock
from skillet.evals import load_evals

from .isolated_home import isolated_home
from .judge import judge_response
from .run_prompt import run_prompt
from .run_script import run_script


async def run_single_eval(  # noqa: C901, PLR0912 - orchestration with cache/script/eval logic
    task: dict,
    name: str,
    skill_path: Path | None,
    allowed_tools: list[str] | None,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
    skip_cache: bool = False,
) -> dict:
    """Run a single evaluation task, using cache if available.

    Every eval runs in an isolated HOME directory. If the task contains
    'setup' or 'teardown' scripts, they are executed before/after the prompts.
    """
    # Check cache first (unless skip_cache is True)
    eval_key = eval_cache_key(task["eval_source"], task["eval_content"])
    cache_dir = get_cache_dir(name, eval_key, skill_path)

    if not skip_cache:
        # Use lock to prevent race condition with parallel workers
        with cache_lock(cache_dir):
            cached = get_cached_iterations(cache_dir)

            # If we have this iteration cached, use it
            if len(cached) >= task["iteration"]:
                result = cached[task["iteration"] - 1]
                result["eval_idx"] = task["eval_idx"]
                result["eval_source"] = task["eval_source"]
                result["cached"] = True
                if on_status:
                    await on_status(task, "cached", result)
                return result

    # Otherwise, run it
    if on_status:
        await on_status(task, "running", None)

    # Determine cwd for scripts (use skill path parent or current dir)
    script_cwd: str | None = None
    if skill_path and ".claude" in skill_path.parts:
        claude_idx = skill_path.parts.index(".claude")
        script_cwd = str(Path(*skill_path.parts[:claude_idx]))

    # Run in isolated HOME environment
    with isolated_home() as home_dir:
        try:
            # Run setup script if present
            if task.get("setup"):
                returncode, stdout, stderr = run_script(task["setup"], home_dir, script_cwd)
                if returncode != 0:
                    result = {
                        "eval_idx": task["eval_idx"],
                        "eval_source": task["eval_source"],
                        "iteration": task["iteration"],
                        "response": f"Setup failed (exit {returncode}): {stderr or stdout}",
                        "judgment": {
                            "pass": False,
                            "reasoning": f"Setup script failed: {stderr or stdout}",
                        },
                        "pass": False,
                        "cached": False,
                    }
                    if on_status:
                        await on_status(task, "done", result)
                    return result

            # Run the eval with isolated HOME
            query_result = await run_prompt(
                task["prompt"], skill_path, allowed_tools, home_dir=home_dir
            )

            # Run teardown script if present (best effort, don't fail the eval)
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)

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
                "response": query_result.text,
                "tool_calls": query_result.tool_calls,
                "judgment": judgment,
                "pass": judgment["pass"],
                "cached": False,
            }

            # Save to cache with lock to prevent race conditions
            # Double-check: another worker may have saved while we were running
            with cache_lock(cache_dir):
                cached = get_cached_iterations(cache_dir)
                if len(cached) < task["iteration"]:
                    # Not yet cached, save our result
                    save_iteration(
                        cache_dir,
                        task["iteration"],
                        {
                            "iteration": task["iteration"],
                            "response": query_result.text,
                            "tool_calls": query_result.tool_calls,
                            "judgment": judgment,
                            "pass": judgment["pass"],
                        },
                    )

            if on_status:
                await on_status(task, "done", result)
            return result
        except (KeyboardInterrupt, SystemExit):
            # Let critical exceptions propagate - don't suppress user interrupts
            # or explicit exit requests
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)
            raise
        except Exception as e:
            # Run teardown on error too (best effort)
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)

            result = {
                "eval_idx": task["eval_idx"],
                "eval_source": task["eval_source"],
                "iteration": task["iteration"],
                "response": str(e),
                "judgment": {
                    "pass": False,
                    "reasoning": f"Error ({type(e).__name__}): {e}",
                },
                "pass": False,
                "cached": False,
            }
            if on_status:
                await on_status(task, "done", result)
            return result


async def evaluate(
    name: str,
    skill_path: Path | None = None,
    samples: int = 3,
    max_evals: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
    skip_cache: bool = False,
) -> dict:
    """Evaluate evals in parallel, with caching.

    Args:
        name: Name of the eval set to evaluate
        skill_path: Optional path to skill directory
        samples: Number of iterations per eval
        max_evals: Maximum number of evals to run (random sample)
        allowed_tools: List of tools to allow
        parallel: Number of parallel workers
        on_status: Optional callback for status updates (task, state, result)
        skip_cache: If True, skip reading from cache (still writes to cache)

    Returns:
        dict with results, pass_rate, and summary statistics
    """
    import random

    evals_list = load_evals(name)
    total_evals = len(evals_list)

    # Sample evals if requested
    if max_evals and max_evals < len(evals_list):
        evals_list = random.sample(evals_list, max_evals)

    # Build task list
    tasks = []
    for eval_idx, eval_data in enumerate(evals_list):
        for i in range(samples):
            task = {
                "eval_idx": eval_idx,
                "eval_source": eval_data["_source"],
                "eval_content": eval_data["_content"],
                "iteration": i + 1,
                "total_iterations": samples,
                "prompt": eval_data["prompt"],
                "expected": eval_data["expected"],
            }
            # Include setup/teardown if present in the eval
            if eval_data.get("setup"):
                task["setup"] = eval_data["setup"]
            if eval_data.get("teardown"):
                task["teardown"] = eval_data["teardown"]
            tasks.append(task)

    # Run with semaphore for parallelism control
    semaphore = asyncio.Semaphore(parallel)

    async def run_with_semaphore(task):
        async with semaphore:
            return await run_single_eval(
                task, name, skill_path, allowed_tools, on_status, skip_cache
            )

    # Run all tasks
    results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

    # Calculate stats
    cached_count = sum(1 for r in results if r.get("cached"))
    fresh_count = len(results) - cached_count
    total_pass = sum(1 for r in results if r["pass"])
    total_runs = len(results)
    pass_rate = total_pass / total_runs * 100 if total_runs > 0 else 0

    return {
        "results": results,
        "tasks": tasks,
        "pass_rate": pass_rate,
        "total_runs": total_runs,
        "total_pass": total_pass,
        "cached_count": cached_count,
        "fresh_count": fresh_count,
        "total_evals": total_evals,
        "sampled_evals": len(evals_list),
    }
