"""Obtain a validated Pydantic model from the selected agent's CLI.

The agent-agnostic counterpart to :func:`skillet._internal.sdk.query_structured`
(which is Claude-SDK only). Instead of the SDK's structured-output protocol,
this asks the agent for a JSON object matching the model's schema and recovers
it from the reply -- so it works for either ``claude`` or ``codex``.
"""

import json
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from skillet.agent import Agent

from .run_agent import run_agent

# Matches a fenced block (```json ... ``` or ``` ... ```), capturing its body.
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)

_MAX_ATTEMPTS = 2

# Appended on a retry, after a reply we could not parse.
_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Reply with ONLY a single raw JSON object and nothing else. "
    "Do not wrap it in markdown fences or add any prose."
)


def _build_prompt(prompt: str, model: type[BaseModel]) -> str:
    """Append a schema instruction so the agent returns matching JSON."""
    schema = json.dumps(model.model_json_schema())
    return (
        f"{prompt}\n\n"
        "Return ONLY a single raw JSON object matching this JSON schema, "
        "with no markdown fences and no prose:\n"
        f"{schema}"
    )


def _extract_json(text: str) -> str:
    """Pull the JSON payload out of an agent reply.

    Handles a raw JSON object, a markdown-fenced block, or a JSON object
    embedded in surrounding prose.
    """
    stripped = text.strip()

    fence = _FENCE_RE.search(stripped)
    if fence:
        return fence.group(1).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]

    return stripped


def _validate_with_unwrap[T: BaseModel](model: type[T], data: Any) -> T:
    """Validate data against a model, unwrapping single-key wrappers.

    Agents sometimes wrap the payload in an extra object layer like
    ``{"output": {...}}``. When validation fails and the data is a single-key
    dict whose value is itself a dict, try the inner value before giving up.
    """
    try:
        return model.model_validate(data)
    except ValidationError:
        if isinstance(data, dict) and len(data) == 1:
            inner = next(iter(data.values()))
            if isinstance(inner, dict):
                return model.model_validate(inner)
        raise


def _parse[T: BaseModel](text: str, model: type[T]) -> T:
    """Parse and validate an agent reply as ``model``, or raise ``ValueError``."""
    payload = _extract_json(text)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Agent did not return valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Agent reply JSON was not an object: {type(data).__name__}")

    try:
        return _validate_with_unwrap(model, data)
    except ValidationError as e:
        raise ValueError(f"Agent reply did not match the {model.__name__} schema: {e}") from e


async def query_structured_via_agent[T: BaseModel](prompt: str, model: type[T], agent: Agent) -> T:
    """Run ``prompt`` through ``agent`` and parse its reply as ``model``.

    The agent is asked for a JSON object matching ``model``'s schema. If the
    first reply cannot be parsed, it is retried once with a stricter
    instruction. Errors from the CLI itself (e.g. a missing executable)
    propagate immediately rather than being retried.

    Raises:
        ValueError: If no valid ``model`` can be parsed after the retry.
    """
    base_prompt = _build_prompt(prompt, model)
    last_error: ValueError | None = None

    for attempt in range(_MAX_ATTEMPTS):
        full_prompt = base_prompt if attempt == 0 else base_prompt + _RETRY_SUFFIX
        result = await run_agent(agent, [full_prompt], allowed_tools=[])
        try:
            return _parse(result.text, model)
        except ValueError as e:
            last_error = e

    raise ValueError(
        f"The {agent.value} agent did not return a valid {model.__name__} "
        f"after a retry: {last_error}"
    )
