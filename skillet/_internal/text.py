"""Text utilities."""


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
