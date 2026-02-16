"""Run evaluations against evals."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet.evals import load_evals

from .run_single_eval import run_single_eval


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

    # Per-eval pass@k and pass^k metrics
    from collections import defaultdict

    from skillet.metrics.pass_at_k import pass_at_k
    from skillet.metrics.pass_pow_k import pass_pow_k

    evals_by_source: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        evals_by_source[r["eval_source"]].append(r)

    per_eval_metrics = []
    for source, eval_results in evals_by_source.items():
        n = len(eval_results)
        c = sum(1 for r in eval_results if r["pass"])
        per_eval_metrics.append(
            {
                "eval_source": source,
                "pass_at_k": pass_at_k(n, c, samples),
                "pass_pow_k": pass_pow_k(n, c, samples),
                "k": samples,
                "n": n,
                "c": c,
            }
        )

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
        "per_eval_metrics": per_eval_metrics,
    }
