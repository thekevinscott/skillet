"""Text utilities."""

MAX_RESPONSE_PREVIEW_LENGTH = 500


def strip_markdown(result: str) -> str:
    """Strip markdown code fences from text."""
    result = result.strip()
    if result.startswith("```markdown"):
        result = result[len("```markdown") :].strip()
    if result.startswith("```"):
        result = result[3:].strip()
    if result.endswith("```"):
        result = result[:-3].strip()
    return result


def truncate_response(text: str | None, max_length: int = MAX_RESPONSE_PREVIEW_LENGTH) -> str:
    """Truncate response text for preview."""
    if not text:
        return ""
    return text[:max_length]


def summarize_failure_for_eval(result: dict) -> dict:
    """Summarize a failure result for eval display.

    Args:
        result: Evaluation result dict with expected, response, judgment keys

    Returns:
        Summary dict suitable for YAML output
    """
    return {
        "expected": result.get("expected", ""),
        "response_preview": truncate_response(result.get("response")),
        "judgment": result.get("judgment", {}).get("reasoning", ""),
    }


def summarize_failure_for_tuning(result: dict) -> dict:
    """Summarize a failure result for skill tuning.

    Args:
        result: Evaluation result dict with prompt, expected, response, judgment keys

    Returns:
        Summary dict suitable for YAML output
    """
    return {
        "prompt": result.get("prompt", ""),
        "expected": result.get("expected", ""),
        "actual_response": truncate_response(result.get("response")),
        "why_failed": result.get("judgment", {}).get("reasoning", ""),
    }
