"""Tests for skill/create module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.errors import SkillError
from skillet.skill.create import create_skill


def describe_create_skill():
    """Tests for create_skill function."""

    @pytest.mark.asyncio
    async def it_raises_error_for_no_evals():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.skill.create.load_evals", return_value=[]),
        ):
            output_dir = Path(tmpdir)
            with pytest.raises(SkillError, match="No eval files found"):
                await create_skill("nonexistent", output_dir)

    @pytest.mark.asyncio
    async def it_raises_error_if_skill_exists_without_overwrite():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.skill.create.load_evals",
                return_value=[{"prompt": "test", "expected": "result"}],
            ),
        ):
            output_dir = Path(tmpdir)
            skill_dir = output_dir / "test-skill"
            skill_dir.mkdir(parents=True)

            with pytest.raises(SkillError, match="already exists"):
                await create_skill("test-skill", output_dir)

    @pytest.mark.asyncio
    async def it_creates_skill_directory():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.skill.create.load_evals",
                return_value=[{"prompt": "test", "expected": "result"}],
            ),
            patch(
                "skillet.skill.create.draft_skill",
                new_callable=AsyncMock,
                return_value="# Test Skill",
            ),
        ):
            output_dir = Path(tmpdir)
            result = await create_skill("my-skill", output_dir)

            assert result["skill_dir"] == output_dir / "my-skill"
            assert result["skill_dir"].exists()
            assert (result["skill_dir"] / "SKILL.md").exists()
            assert result["eval_count"] == 1

    @pytest.mark.asyncio
    async def it_writes_skill_content():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.skill.create.load_evals",
                return_value=[{"prompt": "q", "expected": "a"}],
            ),
            patch(
                "skillet.skill.create.draft_skill",
                new_callable=AsyncMock,
                return_value="---\nname: test\n---\n# Test",
            ),
        ):
            output_dir = Path(tmpdir)
            result = await create_skill("test", output_dir)

            content = (result["skill_dir"] / "SKILL.md").read_text()
            assert "name: test" in content
            assert result["skill_content"] == "---\nname: test\n---\n# Test"

    @pytest.mark.asyncio
    async def it_overwrites_existing_skill_when_flag_set():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.skill.create.load_evals",
                return_value=[{"prompt": "p", "expected": "e"}],
            ),
            patch(
                "skillet.skill.create.draft_skill",
                new_callable=AsyncMock,
                return_value="# New Skill",
            ),
        ):
            output_dir = Path(tmpdir)
            skill_dir = output_dir / "existing"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Old content")

            result = await create_skill("existing", output_dir, overwrite=True)

            content = (result["skill_dir"] / "SKILL.md").read_text()
            assert "# New Skill" in content
            assert "# Old content" not in content

    @pytest.mark.asyncio
    async def it_passes_extra_prompt_to_draft():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "skillet.skill.create.load_evals",
                return_value=[{"prompt": "p", "expected": "e"}],
            ),
            patch("skillet.skill.create.draft_skill", new_callable=AsyncMock) as mock_draft,
        ):
            mock_draft.return_value = "# Skill"
            output_dir = Path(tmpdir)

            await create_skill("test", output_dir, extra_prompt="Be extra terse")

            mock_draft.assert_called_once()
            call_args = mock_draft.call_args
            assert call_args[0][2] == "Be extra terse"
