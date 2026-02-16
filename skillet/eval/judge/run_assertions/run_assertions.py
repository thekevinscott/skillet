"""Grade a response using deterministic code-based assertions."""

from .check_contains import check_contains
from .check_ends_with import check_ends_with
from .check_not_contains import check_not_contains
from .check_regex import check_regex
from .check_starts_with import check_starts_with
from .check_tool_called import check_tool_called
from .check_tool_not_called import check_tool_not_called

_CHECKERS = {
    "contains": check_contains,
    "not_contains": check_not_contains,
    "regex": check_regex,
    "starts_with": check_starts_with,
    "ends_with": check_ends_with,
    "tool_called": check_tool_called,
    "tool_not_called": check_tool_not_called,
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
