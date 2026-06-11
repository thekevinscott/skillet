"""Run the agent under test on a lite-harness backend (e.g. Codex).

lite-harness exposes a Claude Agent SDK-compatible ``query()`` that selects the
agent harness via a ``harness`` option and emits the same streaming message
shapes. It is preview-stage and not published to PyPI, so it is imported lazily
here via :func:`importlib.import_module`: only evals that actually select a
lite-harness backend need it installed, and the type checker does not require
the package to be present.
"""

import importlib
from typing import Any

from skillet.errors import HarnessNotInstalledError

from ..query_result import QueryResult

_INSTALL_HINT = (
    "The 'lite_harness' package is required to run non-Claude harnesses but is "
    "not installed. lite-harness is preview-stage and not on PyPI; install it "
    "from a clone:\n"
    "  git clone https://github.com/LiteLLM-Labs/lite-harness.git\n"
    "  pip install -e lite-harness/src/sdk/python\n"
    "and make Node.js plus the server deps available "
    "(npm install --prefix lite-harness/src/sdk/server)."
)


def _load_lite_harness() -> Any:
    """Import the optional ``lite_harness`` package, or explain how to install it."""
    try:
        return importlib.import_module("lite_harness")
    except ModuleNotFoundError as e:
        raise HarnessNotInstalledError(_INSTALL_HINT) from e


async def run_lite_harness(
    prompts: list[str],
    *,
    harness: str,
    **options: Any,
) -> QueryResult:
    """Run a multi-turn conversation through lite-harness and return the final response."""
    lite = _load_lite_harness()

    session_id: str | None = None
    response_text = ""
    all_tool_calls: list[dict] = []

    for p in prompts:
        response_text = ""
        opts = lite.AgentOptions(
            harness=harness,
            resume=session_id,
            model=options.get("model"),
            cwd=options.get("cwd"),
            max_turns=options.get("max_turns"),
            allowed_tools=options.get("allowed_tools") or [],
            setting_sources=options.get("setting_sources"),
            env=options.get("env") or {},
        )

        async for message in lite.query(prompt=p, options=opts):
            # Capture the session id so subsequent turns resume the conversation.
            if isinstance(message, lite.SystemMessage) and message.subtype == "init":
                sid = message.data.get("session_id")
                if sid:
                    session_id = str(sid)
            if isinstance(message, lite.ResultMessage) and message.session_id:
                session_id = str(message.session_id)

            if isinstance(message, lite.AssistantMessage):
                for block in message.content:
                    if isinstance(block, lite.TextBlock):
                        response_text += block.text
                    elif isinstance(block, lite.ToolUseBlock):
                        all_tool_calls.append(
                            {
                                "name": block.name,
                                "input": block.input,
                            }
                        )

    return QueryResult(
        text=response_text.strip() if response_text else "",
        tool_calls=all_tool_calls,
    )
