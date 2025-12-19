"""Run evaluations against gaps."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from pathlib import Path

from skillet._internal.cache import (
    gap_cache_key,
    get_cache_dir,
    get_cached_iterations,
    save_iteration,
)
from skillet._internal.sdk import QueryResult, query_multiturn
from skillet.config import DEFAULT_SKILL_TOOLS
from skillet.gaps import load_evals

from .judge import judge_response


@contextmanager
def isolated_home() -> Generator[str, None, None]:
    """Context manager for isolated HOME directory.

    Creates a temporary HOME directory for isolated eval execution,
    and ensures cleanup after the eval completes.

    Symlinks ~/.claude to the isolated HOME so Claude CLI can find
    credentials while still isolating other HOME contents like ~/.skillet.

    Yields:
        Path to the temporary HOME directory
    """
    home_dir = tempfile.mkdtemp(prefix="skillet-eval-")
    real_home = os.environ.get("HOME", "")
    try:
        # Symlink ~/.claude for credentials
        real_claude_dir = Path(real_home) / ".claude"
        if real_claude_dir.exists():
            isolated_claude_dir = Path(home_dir) / ".claude"
            isolated_claude_dir.symlink_to(real_claude_dir)
        yield home_dir
    finally:
        if Path(home_dir).exists():
            shutil.rmtree(home_dir, ignore_errors=True)


def run_script(script: str, home_dir: str, cwd: str | None = None) -> tuple[int, str, str]:
    """Run a setup or teardown script with the isolated HOME.

    Args:
        script: Shell script to execute
        home_dir: HOME directory to use
        cwd: Working directory for script execution

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    env = os.environ.copy()
    env["HOME"] = home_dir

    result = subprocess.run(
        ["bash", "-c", script],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout, result.stderr


async def run_prompt(
    prompt: str | list[str],
    skill_path: Path | None = None,
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    home_dir: str | None = None,
) -> QueryResult:
    """Run a prompt (or multi-turn conversation) through Claude and return the response.

    Args:
        prompt: Single prompt string, or list of prompts for multi-turn conversation.
                For multi-turn, each prompt is sent sequentially, resuming the session.
        skill_path: Path to skill directory for Skill tool
        allowed_tools: List of allowed tools
        cwd: Working directory for Claude
        home_dir: Custom HOME directory for isolated execution

    Returns:
        QueryResult with text response and all tool calls made
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

    # Build query options
    query_kwargs: dict = {
        "max_turns": 10,
        "allowed_tools": tools or None,
        "cwd": cwd,
        "setting_sources": ["project"] if cwd else None,
    }

    # Add custom HOME if provided
    if home_dir:
        env = os.environ.copy()
        env["HOME"] = home_dir
        query_kwargs["env"] = env

    result = await query_multiturn(prompts, **query_kwargs)

    if not result.text:
        result.text = "(no text response - Claude may have only used tools)"

    return result


async def run_single_eval(
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
    gap_key = gap_cache_key(task["gap_source"], task["gap_content"])
    cache_dir = get_cache_dir(name, gap_key, skill_path)

    if not skip_cache:
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
                        "gap_idx": task["gap_idx"],
                        "gap_source": task["gap_source"],
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
                "gap_idx": task["gap_idx"],
                "gap_source": task["gap_source"],
                "iteration": task["iteration"],
                "response": query_result.text,
                "tool_calls": query_result.tool_calls,
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
                    "response": query_result.text,
                    "tool_calls": query_result.tool_calls,
                    "judgment": judgment,
                    "pass": judgment["pass"],
                },
            )

            if on_status:
                await on_status(task, "done", result)
            return result
        except Exception as e:
            # Run teardown on error too (best effort)
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)

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
    skip_cache: bool = False,
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
        skip_cache: If True, skip reading from cache (still writes to cache)

    Returns:
        dict with results, pass_rate, and summary statistics
    """
    import random

    evals_list = load_evals(name)
    total_evals = len(evals_list)

    # Sample evals if requested
    if max_gaps and max_gaps < len(evals_list):
        evals_list = random.sample(evals_list, max_gaps)

    # Build task list
    tasks = []
    for eval_idx, eval_data in enumerate(evals_list):
        for i in range(samples):
            task = {
                "gap_idx": eval_idx,
                "gap_source": eval_data["_source"],
                "gap_content": eval_data["_content"],
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
        "total_gaps": total_evals,
        "sampled_gaps": len(evals_list),
    }
