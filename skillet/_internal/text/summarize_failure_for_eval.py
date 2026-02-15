"""Summarize a failure result for eval display."""

from .truncate_response import truncate_response


def summarize_failure_for_eval(result: dict) -> dict:
    """Summarize a failure result for eval display."""
    return {
        "expected": result.get("expected", ""),
        "response_preview": truncate_response(result.get("response")),
        "judgment": result.get("judgment", {}).get("reasoning", ""),
    }
