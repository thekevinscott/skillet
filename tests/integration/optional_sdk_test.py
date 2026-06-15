"""The eval path must not require the optional ``claude_agent_sdk``.

Slice #305: ``claude_agent_sdk`` is an optional extra (``skillet[tune]``).
Importing skillet and running ``skillet eval --agent codex`` end-to-end
(run + judge + summary) must work with the SDK absent.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.agent import Agent
from skillet.cli.commands.eval import eval_command

from .conftest import create_eval_file

# Runs in a fresh interpreter where claude_agent_sdk is forced absent. A None
# entry in sys.modules makes any `import claude_agent_sdk` raise ImportError --
# the same failure a fresh install without the `tune` extra would produce.
_IMPORT_PROBE = """
import sys
sys.modules["claude_agent_sdk"] = None

# The whole eval surface must import without the SDK.
import skillet
import skillet.cli.main
from skillet.cli.commands.eval import eval_command, summarize_responses
from skillet import evaluate, generate_evals
from skillet._internal.agent import query_structured_via_agent, run_agent

# Sanity: the SDK really is unavailable in this process.
try:
    import claude_agent_sdk
except ImportError:
    pass
else:
    raise AssertionError("claude_agent_sdk should have been blocked")

print("EVAL_PATH_IMPORTS_OK")
"""


def _verdict(passed: bool, reasoning: str = "") -> str:
    """A judge verdict as the codex CLI would emit it (agent_message text)."""
    return json.dumps({"pass": passed, "reasoning": reasoning})


def describe_eval_without_claude_sdk():
    """The eval path is independent of the optional Claude SDK."""

    def it_imports_the_eval_path_without_the_sdk():
        """Importing skillet and the eval modules needs no claude_agent_sdk."""
        proc = subprocess.run(
            [sys.executable, "-c", _IMPORT_PROBE],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, (
            "Importing the eval path failed with claude_agent_sdk absent:\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
        assert "EVAL_PATH_IMPORTS_OK" in proc.stdout

    @pytest.mark.asyncio
    async def it_runs_eval_end_to_end_without_the_sdk(skillet_env: Path, mock_codex_cli):
        """eval --agent codex runs, judges, and summarizes with the SDK absent."""
        evals_dir = skillet_env / ".skillet" / "evals" / "no-sdk"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Under parallel=1: agent run, then judge verdict, then the failure
        # summary -- three codex CLI invocations, none touching the SDK.
        mock_codex_cli.set_responses(
            "Wrong answer",
            _verdict(False, "did not meet expectations"),
            json.dumps({"bullets": ["Codex paraphrased the task", "Skipped the required step"]}),
        )

        # Force the SDK absent for the whole run; any runtime import raises.
        with patch.dict(sys.modules, {"claude_agent_sdk": None}):
            await eval_command(
                "no-sdk",
                samples=1,
                parallel=1,
                skip_cache=True,
                agent=Agent.CODEX,
            )

        assert mock_codex_cli.call_count == 3
