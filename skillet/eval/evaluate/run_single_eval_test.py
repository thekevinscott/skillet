"""Tests for run_single_eval."""

from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from cachetta import Cachetta

from skillet._internal.sdk import QueryResult
from skillet.agent import Agent
from skillet.eval.evaluate import run_single_eval

_RSE = "skillet.eval.evaluate.run_single_eval"

# A full success payload as produced by the cacheable leaf, used to model a
# cache hit in the fake below.
_HIT_PAYLOAD = {
    "iteration": 1,
    "response": "cached response",
    "tool_calls": [],
    "judgment": {"pass": True, "reasoning": "cached"},
    "pass": True,
}


class _FakeCache:
    """Stand-in for the iteration Cachetta passed to run_single_eval.

    Pass-through by default: the wrapped function runs and nothing is
    persisted. With a ``hit_payload`` it models a cache hit — ``wrap`` returns
    the payload without running the function. ``copy(read=False)`` (skip_cache)
    drops the hit so the wrapped function always runs.
    """

    def __init__(self, *, hit_payload: dict | None = None):
        self._hit_payload = hit_payload

    def copy(self, *, read: bool = True) -> "_FakeCache":
        return self if read else _FakeCache(hit_payload=None)

    def wrap(self, fn):
        async def wrapper(*args, **kwargs):
            if self._hit_payload is not None:
                return self._hit_payload
            return await fn(*args, **kwargs)

        return wrapper


def _make_task(**overrides) -> dict:
    task = {
        "eval_source": "test.md",
        "eval_content": "content",
        "eval_idx": 0,
        "iteration": 1,
        "prompt": "test",
        "expected": "result",
    }
    task.update(overrides)
    return task


def _passthrough() -> Cachetta:
    return cast(Cachetta, _FakeCache())


def describe_run_single_eval():
    """Tests for run_single_eval function."""

    @pytest.mark.asyncio
    async def it_returns_cached_result_when_available():
        cache = cast(Cachetta, _FakeCache(hit_payload=_HIT_PAYLOAD))

        result = await run_single_eval(_make_task(), None, None, cache, agent=Agent.CLAUDE)

        assert result["cached"] is True
        assert result["response"] == "cached response"

    @pytest.mark.asyncio
    async def it_reports_running_then_cached_for_a_hit():
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        cache = cast(Cachetta, _FakeCache(hit_payload=_HIT_PAYLOAD))

        await run_single_eval(
            _make_task(), None, None, cache, on_status=on_status, agent=Agent.CLAUDE
        )

        # The leaf never runs on a hit, so we only learn it was cached after the
        # decorator returns: status goes running -> cached.
        assert [state for state, _ in status_calls] == ["running", "cached"]

    @pytest.mark.asyncio
    async def it_skips_cache_when_flag_set():
        with (
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="fresh response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            # Cache "has" a hit, but skip_cache must run fresh and ignore it.
            cache = cast(Cachetta, _FakeCache(hit_payload=_HIT_PAYLOAD))

            result = await run_single_eval(
                _make_task(), None, None, cache, skip_cache=True, agent=Agent.CLAUDE
            )

            assert result["cached"] is False
            assert result["response"] == "fresh response"

    @pytest.mark.asyncio
    async def it_handles_setup_script_failure():
        with patch(f"{_RSE}.run_script", return_value=(1, "", "setup failed")):
            task = _make_task(setup="exit 1")

            result = await run_single_eval(task, None, None, _passthrough(), agent=Agent.CLAUDE)

            assert result["pass"] is False
            assert "Setup failed" in result["response"]

    @pytest.mark.asyncio
    async def it_runs_teardown_after_prompt():
        teardown_called = []

        def track_run_script(script, _home_dir, _cwd=None):
            if "teardown" in script:
                teardown_called.append(True)
            return (0, "", "")

        with (
            patch(f"{_RSE}.run_script", side_effect=track_run_script),
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = _make_task(teardown="echo teardown")

            await run_single_eval(task, None, None, _passthrough(), agent=Agent.CLAUDE)

            assert len(teardown_called) == 1

    @pytest.mark.asyncio
    async def it_calls_status_callback_for_running():
        """on_status is called with 'running' then 'done' on a fresh run."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with (
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            await run_single_eval(
                _make_task(), None, None, _passthrough(), on_status=on_status, agent=Agent.CLAUDE
            )

            assert ("running", None) in status_calls
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1

    @pytest.mark.asyncio
    async def it_calls_status_callback_on_setup_failure():
        """on_status is called when the setup script fails."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with patch(f"{_RSE}.run_script", return_value=(1, "", "setup error")):
            task = _make_task(setup="exit 1")

            await run_single_eval(
                task, None, None, _passthrough(), on_status=on_status, agent=Agent.CLAUDE
            )

            assert ("running", None) in status_calls
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1
            assert done_calls[0][1]["pass"] is False

    @pytest.mark.asyncio
    async def it_handles_exception_and_runs_teardown():
        """Teardown runs even when the prompt raises an exception."""
        run_script_calls = []

        def track_run_script(script, _home_dir, _cwd=None):
            run_script_calls.append(script)
            return (0, "", "")

        with (
            patch(f"{_RSE}.run_script", side_effect=track_run_script),
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = RuntimeError("prompt failed")

            task = _make_task(teardown="echo cleanup")

            result = await run_single_eval(task, None, None, _passthrough(), agent=Agent.CLAUDE)

            assert result["pass"] is False
            assert "prompt failed" in result["response"]
            assert "echo cleanup" in run_script_calls

    @pytest.mark.asyncio
    async def it_calls_status_callback_on_exception():
        """on_status is called with done when an exception occurs."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = RuntimeError("prompt failed")

            await run_single_eval(
                _make_task(), None, None, _passthrough(), on_status=on_status, agent=Agent.CLAUDE
            )

            assert ("running", None) in status_calls
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1
            assert done_calls[0][1]["pass"] is False
            assert "prompt failed" in done_calls[0][1]["response"]

    @pytest.mark.asyncio
    async def it_uses_assertions_instead_of_judge():
        with (
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
            patch(f"{_RSE}.run_assertions") as mock_assertions,
        ):
            mock_run.return_value = QueryResult(text="The answer is 4", tool_calls=[])
            mock_assertions.return_value = {"pass": True, "reasoning": "All assertions passed"}

            task = _make_task(assertions=[{"type": "contains", "value": "4"}])

            result = await run_single_eval(task, None, None, _passthrough(), agent=Agent.CLAUDE)

            assert result["pass"] is True
            mock_assertions.assert_called_once()
            mock_judge.assert_not_called()

    @pytest.mark.asyncio
    async def it_falls_back_to_judge_without_assertions():
        with (
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
            patch(f"{_RSE}.run_assertions") as mock_assertions,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            result = await run_single_eval(
                _make_task(), None, None, _passthrough(), agent=Agent.CLAUDE
            )

            assert result["pass"] is True
            mock_judge.assert_called_once()
            mock_assertions.assert_not_called()

    @pytest.mark.asyncio
    async def it_calculates_script_cwd_from_skill_path():
        """script_cwd is derived from the skill path."""
        script_cwd_captured = []

        def capture_run_script(_script, _home_dir, cwd=None):
            script_cwd_captured.append(cwd)
            return (0, "", "")

        with (
            patch(f"{_RSE}.run_script", side_effect=capture_run_script),
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = _make_task(setup="echo setup")
            skill_path = Path("/project/.claude/skills/test")

            await run_single_eval(task, skill_path, None, _passthrough(), agent=Agent.CLAUDE)

            # cwd should be /project (parent of .claude)
            assert script_cwd_captured[0] == "/project"

    @pytest.mark.asyncio
    async def it_calculates_script_cwd_from_codex_skill_path():
        """For --agent codex, script_cwd is derived from the .codex dot-dir."""
        script_cwd_captured = []

        def capture_run_script(_script, _home_dir, cwd=None):
            script_cwd_captured.append(cwd)
            return (0, "", "")

        with (
            patch(f"{_RSE}.run_script", side_effect=capture_run_script),
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
            patch(f"{_RSE}.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = _make_task(setup="echo setup")
            skill_path = Path("/project/.codex/skills/test")

            await run_single_eval(task, skill_path, None, _passthrough(), agent=Agent.CODEX)

            # cwd should be /project (parent of .codex)
            assert script_cwd_captured[0] == "/project"


def describe_exception_handling():
    """Tests for exception handling in run_single_eval."""

    @pytest.mark.asyncio
    async def it_propagates_keyboard_interrupt():
        """KeyboardInterrupt should not be caught - let user cancel."""
        with patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(KeyboardInterrupt):
                await run_single_eval(_make_task(), None, None, _passthrough(), agent=Agent.CLAUDE)

    @pytest.mark.asyncio
    async def it_propagates_system_exit():
        """SystemExit should not be caught - let process exit."""
        with patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = SystemExit(1)

            with pytest.raises(SystemExit):
                await run_single_eval(_make_task(), None, None, _passthrough(), agent=Agent.CLAUDE)

    @pytest.mark.asyncio
    async def it_runs_teardown_on_keyboard_interrupt():
        """Teardown should still run when KeyboardInterrupt is raised."""
        teardown_called = []

        def track_run_script(script, _home_dir, _cwd=None):
            if "teardown" in script:
                teardown_called.append(True)
            return (0, "", "")

        with (
            patch(f"{_RSE}.run_script", side_effect=track_run_script),
            patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = KeyboardInterrupt()

            task = _make_task(teardown="echo teardown")

            with pytest.raises(KeyboardInterrupt):
                await run_single_eval(task, None, None, _passthrough(), agent=Agent.CLAUDE)

            assert len(teardown_called) == 1

    @pytest.mark.asyncio
    async def it_includes_exception_type_in_error_message():
        """Error message should include exception type for debugging."""
        with patch(f"{_RSE}.run_prompt", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = ValueError("invalid value")

            result = await run_single_eval(
                _make_task(), None, None, _passthrough(), agent=Agent.CLAUDE
            )

            assert result["pass"] is False
            assert "ValueError" in result["judgment"]["reasoning"]
            assert "invalid value" in result["judgment"]["reasoning"]
