"""Run prompts through the agent under test."""

import os
from pathlib import Path

from skillet._internal.agent import run_agent
from skillet._internal.sdk import QueryResult
from skillet.agent import Agent
from skillet.config import DEFAULT_SKILL_TOOLS


async def run_prompt(
    prompt: str | list[str],
    skill_path: Path | None = None,
    allowed_tools: list[str] | None = None,
    cwd: str | None = None,
    home_dir: str | None = None,
    *,
    agent: Agent,
) -> QueryResult:
    """Run a prompt (or multi-turn conversation) through the agent and return the response.

    Args:
        prompt: Single prompt string, or list of prompts for multi-turn conversation.
                For multi-turn, each prompt is sent sequentially, resuming the session.
        skill_path: Path to skill directory for Skill tool
        allowed_tools: List of allowed tools
        cwd: Working directory for the agent
        home_dir: Custom HOME directory for isolated execution
        agent: The agent under test (drives the CLI that runs the skill).

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

    # Add custom HOME if provided so the agent runs against an isolated home
    env: dict[str, str] | None = None
    if home_dir:
        env = os.environ.copy()
        env["HOME"] = home_dir

    result = await run_agent(agent, prompts, allowed_tools=tools or None, cwd=cwd, env=env)

    if not result.text:
        result.text = "(no text response - the agent may have only used tools)"

    return result
