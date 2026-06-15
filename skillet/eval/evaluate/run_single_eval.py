"""Run a single evaluation task."""

from collections.abc import Awaitable, Callable
from pathlib import Path

from cachetta import Cachetta

from skillet._internal.cache import INFRA_FAILURE_KEY

from ..isolated_home import isolated_home
from ..judge import judge_response, run_assertions
from ..run_prompt import run_prompt
from ..run_script import run_script


def _script_cwd(skill_path: Path | None) -> str | None:
    """Derive the cwd for setup/teardown scripts from the skill path."""
    if skill_path and ".claude" in skill_path.parts:
        claude_idx = skill_path.parts.index(".claude")
        return str(Path(*skill_path.parts[:claude_idx]))
    return None


async def _run_iteration(
    task: dict, skill_path: Path | None, allowed_tools: list[str] | None
) -> dict:
    """Run one eval iteration in an isolated HOME and return its result payload.

    This is the expensive leaf wrapped by the cachetta decorator. A successful
    run returns ``{iteration, response, tool_calls, judgment, pass}`` (which is
    cached). Setup-script failures and exceptions return a payload tagged with
    ``INFRA_FAILURE_KEY`` so the cache's condition hook keeps them out of the
    cache. ``KeyboardInterrupt``/``SystemExit`` propagate after teardown runs.
    """
    script_cwd = _script_cwd(skill_path)

    with isolated_home() as home_dir:
        try:
            if task.get("setup"):
                returncode, stdout, stderr = run_script(task["setup"], home_dir, script_cwd)
                if returncode != 0:
                    return {
                        "iteration": task["iteration"],
                        "response": f"Setup failed (exit {returncode}): {stderr or stdout}",
                        "judgment": {
                            "pass": False,
                            "reasoning": f"Setup script failed: {stderr or stdout}",
                        },
                        "pass": False,
                        INFRA_FAILURE_KEY: True,
                    }

            query_result = await run_prompt(
                task["prompt"], skill_path, allowed_tools, home_dir=home_dir
            )

            # Run teardown after the prompt (best effort, don't fail the eval)
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)

            if task.get("assertions"):
                judgment = run_assertions(
                    response=query_result.text,
                    assertions=task["assertions"],
                    tool_calls=query_result.tool_calls,
                )
            else:
                judgment = await judge_response(
                    prompt=task["prompt"],
                    response=query_result.text,
                    expected=task["expected"],
                    tool_calls=query_result.tool_calls,
                )

            return {
                "iteration": task["iteration"],
                "response": query_result.text,
                "tool_calls": query_result.tool_calls,
                "judgment": judgment,
                "pass": judgment["pass"],
            }
        except (KeyboardInterrupt, SystemExit):
            # Let critical exceptions propagate - don't suppress user interrupts
            # or explicit exit requests. Still run teardown first (best effort).
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)
            raise
        except Exception as e:
            # Run teardown on error too (best effort)
            if task.get("teardown"):
                run_script(task["teardown"], home_dir, script_cwd)

            return {
                "iteration": task["iteration"],
                "response": str(e),
                "judgment": {
                    "pass": False,
                    "reasoning": f"Error ({type(e).__name__}): {e}",
                },
                "pass": False,
                INFRA_FAILURE_KEY: True,
            }


def _finalize_result(payload: dict, task: dict, *, cached: bool) -> dict:
    """Build the public iteration result from a (cached or fresh) run payload."""
    return {
        "eval_idx": task["eval_idx"],
        "eval_source": task["eval_source"],
        "iteration": payload["iteration"],
        "response": payload["response"],
        "tool_calls": payload.get("tool_calls"),
        "judgment": payload["judgment"],
        "pass": payload["pass"],
        "cached": cached,
    }


async def run_single_eval(
    task: dict,
    skill_path: Path | None,
    allowed_tools: list[str] | None,
    iteration_cache: Cachetta,
    on_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
    skip_cache: bool = False,
) -> dict:
    """Run a single evaluation task, using ``iteration_cache`` for memoization.

    Caching (read/write, atomic writes, in-flight de-duplication) is delegated
    to cachetta's decorator. ``skip_cache`` disables reads (the run always
    executes) while still persisting fresh results, matching prior behavior.

    Whether the result came from cache is derived from whether the wrapped leaf
    actually executed: on a hit the decorator returns the stored payload without
    calling it, so no separate existence check is needed.
    """
    cache = iteration_cache.copy(read=not skip_cache)

    ran = False

    async def _execute(
        task: dict, skill_path: Path | None, allowed_tools: list[str] | None
    ) -> dict:
        nonlocal ran
        ran = True
        return await _run_iteration(task, skill_path, allowed_tools)

    if on_status:
        await on_status(task, "running", None)

    payload = await cache.wrap(_execute)(task, skill_path, allowed_tools)
    cached = not ran
    result = _finalize_result(payload, task, cached=cached)
    if on_status:
        await on_status(task, "cached" if cached else "done", result)
    return result
