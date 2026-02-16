"""Grade a response using deterministic code-based assertions."""

import re


def _check_contains(value: str, response_lower: str, **_: object) -> str | None:
    if value.lower() not in response_lower:
        return f"contains: expected response to contain '{value}'"
    return None


def _check_not_contains(value: str, response_lower: str, **_: object) -> str | None:
    if value.lower() in response_lower:
        return f"not_contains: expected response NOT to contain '{value}'"
    return None


def _check_regex(value: str, response: str, **_: object) -> str | None:
    try:
        if not re.search(value, response):
            return f"regex: pattern '{value}' did not match"
    except re.error as e:
        return f"regex: invalid pattern '{value}': {e}"
    return None


def _check_starts_with(value: str, response_lower: str, **_: object) -> str | None:
    if not response_lower.startswith(value.lower()):
        return f"starts_with: expected response to start with '{value}'"
    return None


def _check_ends_with(value: str, response_lower: str, **_: object) -> str | None:
    if not response_lower.rstrip().endswith(value.lower()):
        return f"ends_with: expected response to end with '{value}'"
    return None


def _check_tool_called(value: str, tool_names: set[str], **_: object) -> str | None:
    if value not in tool_names:
        return f"tool_called: expected tool '{value}' to be called"
    return None


def _check_tool_not_called(value: str, tool_names: set[str], **_: object) -> str | None:
    if value in tool_names:
        return f"tool_not_called: expected tool '{value}' NOT to be called"
    return None


_CHECKERS = {
    "contains": _check_contains,
    "not_contains": _check_not_contains,
    "regex": _check_regex,
    "starts_with": _check_starts_with,
    "ends_with": _check_ends_with,
    "tool_called": _check_tool_called,
    "tool_not_called": _check_tool_not_called,
}


def run_assertions(
    response: str,
    assertions: list[dict],
    tool_calls: list[dict] | None = None,
) -> dict:
    """Evaluate response against a list of assertions.

    All assertions must pass (AND semantics). Returns the same shape as
    ``judge_response()`` so callers can use either interchangeably.
    """
    failures: list[str] = []
    response_lower = response.lower()
    tool_names = {tc.get("name", "") for tc in (tool_calls or [])}

    for assertion in assertions:
        checker = _CHECKERS[assertion["type"]]
        failure = checker(
            value=assertion.get("value", ""),
            response=response,
            response_lower=response_lower,
            tool_names=tool_names,
        )
        if failure:
            failures.append(failure)

    passed = len(failures) == 0
    reasoning = "All assertions passed" if passed else "; ".join(failures)

    return {"pass": passed, "reasoning": reasoning}
