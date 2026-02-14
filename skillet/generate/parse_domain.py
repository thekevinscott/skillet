"""Domain string parsing for LLM output."""

from .types import EvalDomain


def parse_domain(value: str) -> EvalDomain | None:
    """Parse a domain string from LLM output into an EvalDomain enum."""
    try:
        return EvalDomain(value.lower().strip())
    except ValueError:
        return None
