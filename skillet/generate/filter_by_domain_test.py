"""Tests for domain filtering."""

from skillet.generate.filter_by_domain import filter_by_domain
from skillet.generate.types import CandidateEval, EvalDomain


def describe_filter_by_domain():
    def it_returns_all_when_domains_is_none():
        candidates = [
            CandidateEval(
                "p1", "e1", "n1", "positive", "s1", 0.8, "r1", domain=EvalDomain.TRIGGERING
            ),
            CandidateEval(
                "p2", "e2", "n2", "positive", "s2", 0.8, "r2", domain=EvalDomain.FUNCTIONAL
            ),
        ]
        result = filter_by_domain(candidates, domains=None)
        assert len(result) == 2

    def it_filters_to_requested_domains():
        candidates = [
            CandidateEval(
                "p1", "e1", "n1", "positive", "s1", 0.8, "r1", domain=EvalDomain.TRIGGERING
            ),
            CandidateEval(
                "p2", "e2", "n2", "positive", "s2", 0.8, "r2", domain=EvalDomain.FUNCTIONAL
            ),
            CandidateEval(
                "p3", "e3", "n3", "positive", "s3", 0.8, "r3", domain=EvalDomain.PERFORMANCE
            ),
        ]
        result = filter_by_domain(candidates, domains=[EvalDomain.TRIGGERING])
        assert len(result) == 1
        assert result[0].domain == EvalDomain.TRIGGERING

    def it_accepts_multiple_domains():
        candidates = [
            CandidateEval(
                "p1", "e1", "n1", "positive", "s1", 0.8, "r1", domain=EvalDomain.TRIGGERING
            ),
            CandidateEval(
                "p2", "e2", "n2", "positive", "s2", 0.8, "r2", domain=EvalDomain.FUNCTIONAL
            ),
            CandidateEval(
                "p3", "e3", "n3", "positive", "s3", 0.8, "r3", domain=EvalDomain.PERFORMANCE
            ),
        ]
        result = filter_by_domain(
            candidates, domains=[EvalDomain.TRIGGERING, EvalDomain.FUNCTIONAL]
        )
        assert len(result) == 2

    def it_excludes_candidates_with_none_domain():
        candidates = [
            CandidateEval(
                "p1", "e1", "n1", "positive", "s1", 0.8, "r1", domain=EvalDomain.TRIGGERING
            ),
            CandidateEval("p2", "e2", "n2", "positive", "s2", 0.8, "r2", domain=None),
        ]
        result = filter_by_domain(candidates, domains=[EvalDomain.TRIGGERING])
        assert len(result) == 1
