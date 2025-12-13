"""Run evaluations against gaps."""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from skillet._internal.cache import (
    gap_cache_key,
    get_cache_dir,
    get_cached_iterations,
    save_iteration,
)
from skillet._internal.sdk import query_multiturn
from skillet.config import DEFAULT_SKILL_TOOLS
from skillet.gaps import load_gaps

from .judge import judge_response


async def run_prompt(
    prompt: str | list[str],
    skill_path: Path | None = None,
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
) -> str:
    """Run a prompt (or multi-turn conversation) through Claude and return the response.

    Args:
        prompt: Single prompt string, or list of prompts for multi-turn conversation.
                For multi-turn, each prompt is sent sequentially, resuming the session.
        skill_path: Path to skill directory for Skill tool
        allowed_tools: List of allowed tools
        cwd: Working directory for Claude

    Returns:
        The final assistant response text
    """
    # Normalize to list
    prompts = [prompt] if isinstance(prompt, str) else prompt

    # If skill path provided and no cwd, set cwd to parent of .claude/skills
    if cwd is None and skill_path and ".claude" in skill_path.parts:
        claude_idx = skill_path.parts.index(".claude")
        cwd = str(Path(*skill_path.parts[:claude_idx]))

    # Build allowed_tools, ensuring Skill is included if we have a skill
    tools: list[str]
    if skill_path:
        if allowed_tools is not None and "Skill" not in allowed_tools:
            tools = ["Skill", *list(allowed_tools)]
        elif allowed_tools is None:
            tools = list(DEFAULT_SKILL_TOOLS)
        else:
            tools = list(allowed_tools)
    else:
        tools = list(allowed_tools) if allowed_tools else []

    response_text = await query_multiturn(
        prompts,
        max_turns=10,
        allowed_tools=tools or None,
        cwd=cwd,
        setting_sources=["project"] if cwd else None,
    )

    if not response_text:
        response_text = "(no text response - Claude may have only used tools)"

    return response_text


async def run_single_eval(
    task: dict,
    name: str,
    skill_path: Path | None,
    allowed_tools: list[str] | None,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
) -> dict:
    """Run a single evaluation task, using cache if available."""
    # Check cache first
    gap_key = gap_cache_key(task["gap_source"], task["gap_content"])
    cache_dir = get_cache_dir(name, gap_key, skill_path)
    cached = get_cached_iterations(cache_dir)

    # If we have this iteration cached, use it
    if len(cached) >= task["iteration"]:
        result = cached[task["iteration"] - 1]
        result["gap_idx"] = task["gap_idx"]
        result["gap_source"] = task["gap_source"]
        result["cached"] = True
        if on_status:
            await on_status(task, "cached", result)
        return result

    # Otherwise, run it
    if on_status:
        await on_status(task, "running", None)

    try:
        response = await run_prompt(task["prompt"], skill_path, allowed_tools)
        judgment = await judge_response(
            prompt=task["prompt"],
            response=response,
            expected=task["expected"],
        )

        result = {
            "gap_idx": task["gap_idx"],
            "gap_source": task["gap_source"],
            "iteration": task["iteration"],
            "response": response,
            "judgment": judgment,
            "pass": judgment["pass"],
            "cached": False,
        }

        # Save to cache
        save_iteration(
            cache_dir,
            task["iteration"],
            {
                "iteration": task["iteration"],
                "response": response,
                "judgment": judgment,
                "pass": judgment["pass"],
            },
        )

        if on_status:
            await on_status(task, "done", result)
        return result
    except Exception as e:
        result = {
            "gap_idx": task["gap_idx"],
            "gap_source": task["gap_source"],
            "iteration": task["iteration"],
            "response": str(e),
            "judgment": {"pass": False, "reasoning": f"Error: {e}"},
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
    max_gaps: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
) -> dict:
    """Evaluate gaps in parallel, with caching.

    Args:
        name: Name of the gap set to evaluate
        skill_path: Optional path to skill directory
        samples: Number of iterations per gap
        max_gaps: Maximum number of gaps to evaluate (random sample)
        allowed_tools: List of tools to allow
        parallel: Number of parallel workers
        on_status: Optional callback for status updates (task, state, result)

    Returns:
        dict with results, pass_rate, and summary statistics
    """
    import random

    gaps = load_gaps(name)
    total_gaps = len(gaps)

    # Sample gaps if requested
    if max_gaps and max_gaps < len(gaps):
        gaps = random.sample(gaps, max_gaps)

    # Build task list
    tasks = []
    for gap_idx, gap in enumerate(gaps):
        for i in range(samples):
            tasks.append(
                {
                    "gap_idx": gap_idx,
                    "gap_source": gap["_source"],
                    "gap_content": gap["_content"],
                    "iteration": i + 1,
                    "total_iterations": samples,
                    "prompt": gap["prompt"],
                    "expected": gap["expected"],
                }
            )

    # Run with semaphore for parallelism control
    semaphore = asyncio.Semaphore(parallel)

    async def run_with_semaphore(task):
        async with semaphore:
            return await run_single_eval(task, name, skill_path, allowed_tools, on_status)

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
        "total_gaps": total_gaps,
        "sampled_gaps": len(gaps),
    }
