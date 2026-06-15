"""Parse an agent's verdict text into a validated Judgment."""

import json
import re

from pydantic import ValidationError

from .types import Judgment

# Matches a fenced block (```json ... ``` or ``` ... ```), capturing its body.
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


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


def parse_judgment(text: str) -> Judgment:
    """Parse and validate an agent's verdict text as a :class:`Judgment`.

    Accepts a raw JSON object, a markdown-fenced block, or a JSON object
    embedded in prose. Raises ``ValueError`` if no JSON object matching the
    verdict schema can be recovered.
    """
    payload = _extract_json(text)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Judge did not return valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Judge verdict JSON was not an object: {type(data).__name__}")

    try:
        return Judgment.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Judge verdict did not match the schema: {e}") from e
