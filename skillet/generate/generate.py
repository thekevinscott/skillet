"""LLM-based eval generation from skill analysis."""

from pathlib import Path

from pydantic import BaseModel

from skillet._internal.sdk import query_structured
from skillet.prompts import load_prompt

from .analyze import SkillAnalysis
from .types import ALL_DOMAINS, CandidateEval, EvalDomain, SkippedDomain


class CandidateResponse(BaseModel):
    """Single candidate eval from LLM response."""

    prompt: str
    expected: str
    name: str
    category: str
    source: str
    confidence: float
    rationale: str
    domain: str = "functional"


class SkippedDomainResponse(BaseModel):
    """A domain the model couldn't generate viable evals for."""

    domain: str
    reason: str


class GenerateResponse(BaseModel):
    """LLM response containing generated candidates."""

    candidates: list[CandidateResponse]
    skipped_domains: list[SkippedDomainResponse] = []


GENERATE_PROMPT = Path(__file__).parent / "generate.txt"

_VALID_DOMAINS = {d.value for d in EvalDomain}


def _try_lint(skill_path: Path) -> list[dict] | None:
    """Try to run linter on skill, returning findings or None if unavailable."""
    try:
        from skillet.lint import lint  # type: ignore[import-not-found]

        result = lint(skill_path)
        return [
            {
                "rule_id": f.rule_id,
                "message": f.message,
                "severity": f.severity.value,
                "line": f.line,
                "suggestion": f.suggestion,
            }
            for f in result.findings
        ]
    except ImportError:
        return None


async def generate_candidates(
    analysis: SkillAnalysis,
    *,
    use_lint: bool = True,
    max_per_category: int = 5,
    domains: frozenset[EvalDomain] = ALL_DOMAINS,
) -> tuple[list[CandidateEval], list[SkippedDomain]]:
    """Generate candidate evals using LLM based on skill analysis.

    Returns a tuple of (candidates, skipped_domains).
    """
    # Prepare context for LLM
    goals_text = "\n".join(f"- Goal {i + 1}: {g}" for i, g in enumerate(analysis.goals))
    prohibitions_text = "\n".join(
        f"- Prohibition {i + 1}: {p}" for i, p in enumerate(analysis.prohibitions)
    )
    examples_text = "\n".join(f"```\n{e}\n```" for e in analysis.examples[:3])

    # Try to get lint findings
    lint_findings_text = ""
    if use_lint:
        findings = _try_lint(analysis.path)
        if findings:
            lint_findings_text = "\n".join(
                f"- Line {f.get('line', '?')}: [{f['rule_id']}] {f['message']}" for f in findings
            )

    # Build category instructions
    categories = ["positive (happy-path scenarios)", "negative (should-not-trigger scenarios)"]
    if lint_findings_text:
        categories.append("ambiguity (targeting lint findings)")

    categories_text = ", ".join(categories)

    # Build domain instructions
    domain_names = sorted(d.value for d in domains)
    domains_text = ", ".join(domain_names)

    prompt = load_prompt(
        GENERATE_PROMPT,
        skill_name=analysis.name or "unnamed",
        skill_description=analysis.description or "No description",
        goals=goals_text or "No explicit goals found",
        prohibitions=prohibitions_text or "No explicit prohibitions found",
        examples=examples_text or "No examples found",
        lint_findings=lint_findings_text or "No lint findings",
        categories=categories_text,
        max_per_category=str(max_per_category),
        domains=domains_text,
    )

    # Query LLM with structured output, retrying once if the model
    # exhausts its output budget on text without producing the
    # StructuredOutput tool call.
    try:
        response = await query_structured(prompt, GenerateResponse)
    except ValueError:
        response = await query_structured(prompt, GenerateResponse)

    # Convert to CandidateEval objects, filtering to requested domains
    candidates = [
        CandidateEval(
            prompt=c.prompt,
            expected=c.expected,
            name=c.name,
            category=c.category,
            source=c.source,
            confidence=c.confidence,
            rationale=c.rationale,
            domain=c.domain if c.domain in _VALID_DOMAINS else "functional",
        )
        for c in response.candidates
        if c.domain in {d.value for d in domains}
    ]

    # Convert skipped domains
    skipped = [
        SkippedDomain(domain=s.domain, reason=s.reason)
        for s in response.skipped_domains
        if s.domain in _VALID_DOMAINS
    ]

    # Apply max_per_category limit
    return _limit_by_category(candidates, max_per_category), skipped


def _limit_by_category(
    candidates: list[CandidateEval], max_per_category: int
) -> list[CandidateEval]:
    """Limit candidates to max_per_category per category."""
    counts: dict[str, int] = {}
    result = []

    for c in candidates:
        count = counts.get(c.category, 0)
        if count < max_per_category:
            result.append(c)
            counts[c.category] = count + 1

    return result
