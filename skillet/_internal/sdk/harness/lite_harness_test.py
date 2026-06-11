"""Tests for the lite-harness adapter (the agent-under-test backend for Codex)."""

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from skillet._internal.sdk.harness import lite_harness
from skillet.errors import HarnessNotInstalledError


# Fakes mirroring the lite-harness message / option shapes (it is not installed).
@dataclass
class _Text:
    text: str


@dataclass
class _ToolUse:
    id: str
    name: str
    input: dict


@dataclass
class _Assistant:
    content: list
    model: str = ""


@dataclass
class _System:
    subtype: str
    data: dict


@dataclass
class _Result:
    session_id: str = ""
    subtype: str = "success"


class _Options:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _fake_module(turn_messages, calls):
    """Build a fake ``lite_harness`` module yielding ``turn_messages`` per turn."""
    turns = iter(turn_messages)

    async def query(*, prompt, options):
        calls.append({"prompt": prompt, "options": options})
        for msg in next(turns):
            yield msg

    return SimpleNamespace(
        AgentOptions=_Options,
        query=query,
        TextBlock=_Text,
        ToolUseBlock=_ToolUse,
        AssistantMessage=_Assistant,
        SystemMessage=_System,
        ResultMessage=_Result,
    )


def describe_run_lite_harness():
    @pytest.mark.asyncio
    async def it_collects_text_and_tool_calls():
        calls: list = []
        messages = [
            [
                _Assistant(content=[_Text("Ahoy "), _ToolUse("1", "Read", {"path": "/x"})]),
                _Assistant(content=[_Text("matey")]),
                _Result(session_id="s1"),
            ]
        ]
        fake = _fake_module(messages, calls)
        with patch.object(lite_harness, "_load_lite_harness", return_value=fake):
            result = await lite_harness.run_lite_harness(["hello"], harness="codex")

        assert result.text == "Ahoy matey"
        assert result.tool_calls == [{"name": "Read", "input": {"path": "/x"}}]

    @pytest.mark.asyncio
    async def it_passes_harness_and_options_to_agent_options():
        calls: list = []
        with patch.object(
            lite_harness, "_load_lite_harness", return_value=_fake_module([[_Result()]], calls)
        ):
            await lite_harness.run_lite_harness(
                ["hello"], harness="codex", cwd="/work", max_turns=7, allowed_tools=["Read"]
            )

        opts = calls[0]["options"].kwargs
        assert opts["harness"] == "codex"
        assert opts["cwd"] == "/work"
        assert opts["max_turns"] == 7
        assert opts["allowed_tools"] == ["Read"]

    @pytest.mark.asyncio
    async def it_resumes_the_session_on_later_turns():
        calls: list = []
        messages = [
            [_System(subtype="init", data={"session_id": "sess-9"}), _Result(session_id="sess-9")],
            [_Assistant(content=[_Text("second")]), _Result(session_id="sess-9")],
        ]
        fake = _fake_module(messages, calls)
        with patch.object(lite_harness, "_load_lite_harness", return_value=fake):
            result = await lite_harness.run_lite_harness(["one", "two"], harness="codex")

        assert calls[0]["options"].kwargs["resume"] is None
        assert calls[1]["options"].kwargs["resume"] == "sess-9"
        assert result.text == "second"

    @pytest.mark.asyncio
    async def it_raises_when_lite_harness_is_not_installed():
        with (
            patch.object(
                lite_harness.importlib,
                "import_module",
                side_effect=ModuleNotFoundError("lite_harness"),
            ),
            pytest.raises(HarnessNotInstalledError, match="not installed"),
        ):
            await lite_harness.run_lite_harness(["hello"], harness="codex")
