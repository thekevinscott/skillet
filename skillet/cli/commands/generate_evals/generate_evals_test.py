"""Tests for generate_evals_command."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from rich.console import Console

from skillet.generate.types import CandidateEval, GenerateResult

from .generate_evals import generate_evals_command

_MODULE = "skillet.cli.commands.generate_evals.generate_evals"


def _make_result(skill_path: Path) -> GenerateResult:
    return GenerateResult(
        skill_path=skill_path,
        candidates=[
            CandidateEval(
                prompt="Test",
                expected="Result",
                name="test",
                category="positive",
                source="goal:1",
                confidence=0.9,
                rationale="Test",
            ),
        ],
        analysis={"name": "test-skill", "goals": [], "prohibitions": [], "example_count": 0},
    )


def describe_generate_evals_command():
    @pytest.fixture(autouse=True)
    def mock_generate(tmp_path):
        skill_path = tmp_path / "SKILL.md"
        with patch(
            f"{_MODULE}.generate_evals",
            new_callable=AsyncMock,
            return_value=_make_result(skill_path),
        ) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_console():
        with patch(f"{_MODULE}.console", Console(file=Path("/dev/null").open("w"))):
            yield

    @pytest.mark.asyncio
    async def it_defaults_output_to_candidates_subdir(tmp_path: Path, mock_generate):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("# Skill")

        await generate_evals_command(skill_path)

        assert mock_generate.call_args.kwargs["output_dir"] == tmp_path / "candidates"
