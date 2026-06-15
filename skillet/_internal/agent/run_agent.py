"""Dispatch a prompt to the selected agent's CLI runner."""

from skillet._internal.sdk.query_result import QueryResult
from skillet.agent import Agent

from .run_claude_cli import run_claude_cli


async def run_agent(
    agent: Agent,
    prompts: list[str],
    *,
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> QueryResult:
    """Run ``prompts`` through the CLI of the selected ``agent``.

    Args:
        agent: The agent under test.
        prompts: One prompt per turn.
        allowed_tools: Tools to pre-approve.
        cwd: Working directory for the CLI (the eval sandbox).
        env: Environment for the subprocess (e.g. an isolated ``HOME``).

    Raises:
        NotImplementedError: If ``agent`` is recognized but not yet wired up.
    """
    if agent is Agent.CLAUDE:
        return await run_claude_cli(prompts, allowed_tools=allowed_tools, cwd=cwd, env=env)
    if agent is Agent.CODEX:
        raise NotImplementedError(
            "The 'codex' agent is not yet supported. Use --agent claude for now."
        )
    raise ValueError(f"Unknown agent: {agent!r}")  # pragma: no cover
