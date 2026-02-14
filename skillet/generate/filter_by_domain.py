"""Domain filtering for eval candidates."""

from .types import CandidateEval, EvalDomain


def filter_by_domain(
    candidates: list[CandidateEval], domains: list[EvalDomain] | None
) -> list[CandidateEval]:
    """Filter candidates to only include requested domains. None means all."""
    if domains is None:
        return candidates
    domain_set = set(domains)
    return [c for c in candidates if c.domain in domain_set]
