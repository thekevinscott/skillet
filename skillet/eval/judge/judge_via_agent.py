"""Obtain a judge verdict from the selected agent's CLI."""

from skillet._internal.agent import run_agent
from skillet.agent import Agent
from skillet.errors import JudgeError

from .parse_judgment import parse_judgment
from .types import Judgment

# Appended to the judge prompt on a retry, after a reply we could not parse.
_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Reply with ONLY a single raw JSON object and nothing else, "
    'for example {"pass": true, "reasoning": "..."}. '
    "Do not wrap it in markdown fences or add any prose."
)

_MAX_ATTEMPTS = 2


async def judge_via_agent(judge_prompt: str, agent: Agent) -> Judgment:
    """Run ``judge_prompt`` through ``agent`` and parse its reply as a verdict.

    The agent is asked for a JSON object matching :class:`Judgment`. If the
    first reply is not valid JSON, it is retried once with a stricter
    instruction. Errors from the CLI itself (e.g. a missing or failing
    executable) propagate immediately rather than being retried.

    Raises:
        JudgeError: If no valid verdict can be parsed after the retry.
    """
    last_error: ValueError | None = None

    for attempt in range(_MAX_ATTEMPTS):
        prompt = judge_prompt if attempt == 0 else judge_prompt + _RETRY_SUFFIX
        result = await run_agent(agent, [prompt], allowed_tools=[])
        try:
            return parse_judgment(result.text)
        except ValueError as e:
            last_error = e

    raise JudgeError(
        f"The {agent.value} judge did not return a valid verdict after a retry: {last_error}"
    )
