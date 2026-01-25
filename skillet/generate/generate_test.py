"""Unit tests for generate module."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.generate.analyze import SkillAnalysis
from skillet.generate.generate import (
    CandidateResponse,
    GenerateResponse,
    _limit_by_category,
    generate_candidates,
)
from skillet.generate.types import CandidateEval


@pytest.mark.parametrize(
    ("candidates", "max_per_category", "expected_positive", "expected_negative"),
    [
        (
            [
                CandidateEval("p1", "e1", "n1", "positive", "s1", 0.8, "r1"),
                CandidateEval("p2", "e2", "n2", "positive", "s2", 0.8, "r2"),
                CandidateEval("p3", "e3", "n3", "positive", "s3", 0.8, "r3"),
                CandidateEval("p4", "e4", "n4", "negative", "s4", 0.8, "r4"),
                CandidateEval("p5", "e5", "n5", "negative", "s5", 0.8, "r5"),
            ],
            2,
            2,
            2,
        ),
        (
            [
                CandidateEval("p1", "e1", "n1", "positive", "s1", 0.8, "r1"),
            ],
            5,
            1,
            0,
        ),
    ],
    ids=["limits-per-category", "fewer-than-limit"],
)
def test_limit_by_category(
    candidates: list[CandidateEval],
    max_per_category: int,
    expected_positive: int,
    expected_negative: int,
):
    """Applies limit per category, not globally."""
    result = _limit_by_category(candidates, max_per_category)

    positive_count = sum(1 for c in result if c.category == "positive")
    negative_count = sum(1 for c in result if c.category == "negative")

    assert positive_count == expected_positive
    assert negative_count == expected_negative


def describe_limit_by_category():
    """Tests for _limit_by_category."""

    def it_preserves_order():
        """Keeps candidates in original order within limit."""
        candidates = [
            CandidateEval("first", "e1", "n1", "positive", "s1", 0.8, "r1"),
            CandidateEval("second", "e2", "n2", "positive", "s2", 0.8, "r2"),
            CandidateEval("third", "e3", "n3", "positive", "s3", 0.8, "r3"),
        ]

        result = _limit_by_category(candidates, max_per_category=2)

        assert result[0].prompt == "first"
        assert result[1].prompt == "second"


def _make_response(*candidates_data: dict) -> GenerateResponse:
    """Helper to create a GenerateResponse from candidate dicts."""
    candidates = [
        CandidateResponse(
            prompt=c.get("prompt", "test prompt"),
            expected=c.get("expected", "test expected"),
            name=c.get("name", "test"),
            category=c.get("category", "positive"),
            source=c.get("source", "goal:1"),
            confidence=c.get("confidence", 0.8),
            rationale=c.get("rationale", "test rationale"),
        )
        for c in candidates_data
    ]
    return GenerateResponse(candidates=candidates)


def describe_generate_candidates():
    """Tests for generate_candidates."""

    @pytest.mark.asyncio
    async def it_generates_evals_from_analysis():
        """Generates candidates from skill analysis."""
        analysis = SkillAnalysis(
            path=Path("/tmp/SKILL.md"),
            name="test-skill",
            description="A test skill",
            goals=["Do something useful"],
            prohibitions=["Never do bad things"],
        )

        mock_response = _make_response(
            {
                "prompt": "Generated prompt",
                "expected": "Expected behavior",
                "name": "test-1",
                "category": "positive",
                "source": "goal:1",
                "confidence": 0.9,
                "rationale": "Tests goal 1",
            }
        )

        with patch(
            "skillet.generate.generate.query_structured",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await generate_candidates(analysis)

        assert len(result) == 1
        assert result[0].prompt == "Generated prompt"

    @pytest.mark.asyncio
    async def it_applies_max_per_category():
        """Respects max_per_category limit."""
        analysis = SkillAnalysis(
            path=Path("/tmp/SKILL.md"),
            name="test",
            goals=["Goal 1"],
        )

        mock_response = _make_response(
            *[{"name": f"n{i}", "category": "positive"} for i in range(10)]
        )

        with patch(
            "skillet.generate.generate.query_structured",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await generate_candidates(analysis, max_per_category=3)

        positive_count = sum(1 for c in result if c.category == "positive")
        assert positive_count <= 3

    @pytest.mark.asyncio
    async def it_handles_lint_unavailable():
        """Works when lint module is not available."""
        analysis = SkillAnalysis(
            path=Path("/tmp/SKILL.md"),
            name="test",
            goals=["Goal 1"],
        )

        mock_response = _make_response({"name": "test"})

        with (
            patch(
                "skillet.generate.generate.query_structured",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
            patch(
                "skillet.generate.generate._try_lint",
                return_value=None,
            ),
        ):
            result = await generate_candidates(analysis, use_lint=True)

        assert len(result) == 1
