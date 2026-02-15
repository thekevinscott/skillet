"""Run eval iterations for tuning."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet.eval import judge_response, run_prompt


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
