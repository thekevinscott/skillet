"""Summarize a failure result for skill tuning."""

from .truncate_response import truncate_response


def summarize_failure_for_tuning(result: dict) -> dict:
    """Summarize a failure result for skill tuning."""
    return {
        "prompt": result.get("prompt", ""),
        "expected": result.get("expected", ""),
        "actual_response": truncate_response(result.get("response")),
        "why_failed": result.get("judgment", {}).get("reasoning", ""),
    }
