"""Run a prompt (or multi-turn conversation) through the Codex CLI."""

from asyncio import create_subprocess_exec
from asyncio.subprocess import DEVNULL, PIPE
from shutil import which

from skillet._internal.sdk.query_result import QueryResult

from .parse_codex_stream import parse_codex_stream

# Flags shared by the initial `exec` and subsequent `exec resume` turns.
_BASE_FLAGS = ["--json", "--skip-git-repo-check"]

# Codex governs tool access through its sandbox policy rather than a per-tool
# allowlist. Evals run in an isolated, throwaway HOME, so grant workspace writes.
_SANDBOX_MODE = "workspace-write"


async def run_codex_cli(
    prompts: list[str],
    *,
    allowed_tools: list[str] | None = None,  # noqa: ARG001 - codex has no per-tool allowlist
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> QueryResult:
    """Drive the `codex` CLI as the agent under test and return its response.

    The first prompt runs as ``codex exec``; subsequent turns ``codex exec
    resume <thread_id>`` so multi-turn evals keep their context. Run in ``cwd``
    (passed as ``-C``) so the CLI auto-loads ``.codex/skills`` from the sandbox.

    ``allowed_tools`` is accepted for interface symmetry with the claude runner
    but ignored: codex controls tool access via its sandbox mode, not a per-tool
    allowlist.

    Raises:
        RuntimeError: If the `codex` CLI is missing from PATH, a turn reports a
            failure (``turn.failed``/``error``), or a turn exits non-zero without
            producing any text.
    """
    if which("codex") is None:
        raise RuntimeError(
            "The 'codex' CLI was not found on PATH. Install Codex to run evals with --agent codex."
        )

    thread_id: str | None = None
    response_text = ""
    all_tool_calls: list[dict] = []

    for prompt in prompts:
        cmd = ["codex", "exec"]
        if thread_id:
            cmd += ["resume", thread_id, *_BASE_FLAGS]
        else:
            cmd += [*_BASE_FLAGS, "-s", _SANDBOX_MODE]
            if cwd:
                cmd += ["-C", cwd]
        cmd.append(prompt)

        proc = await create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout, stderr = await proc.communicate()

        text, tool_calls, turn_thread_id, error = parse_codex_stream(stdout.decode())

        if error:
            raise RuntimeError(f"codex turn failed: {error}")

        if proc.returncode != 0 and not text:
            err = stderr.decode().strip()
            raise RuntimeError(
                f"codex exited with code {proc.returncode}" + (f": {err}" if err else "")
            )

        if turn_thread_id:
            thread_id = turn_thread_id
        response_text = text
        all_tool_calls.extend(tool_calls)

    return QueryResult(text=response_text, tool_calls=all_tool_calls)
