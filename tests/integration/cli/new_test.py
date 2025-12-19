"""Integration tests for the `skillet new` command."""

from pathlib import Path

import pytest

from skillet.errors import EmptyFolderError, EvalValidationError, SkillError
from skillet.skill.create import create_skill

VALID_SKILL_RESPONSE = """---
name: test-skill
description: A test skill for integration testing
---

# Test Skill

Instructions for the test skill.
"""


def _create_eval_file(path: Path, **overrides) -> None:
    """Create a valid eval YAML file with optional field overrides."""
    defaults = {
        "timestamp": "2025-01-01T00:00:00Z",
        "prompt": "Test prompt",
        "expected": "Test expected behavior",
        "name": "test-skill",
    }
    defaults.update(overrides)

    lines = [f"{k}: {v!r}" if isinstance(v, str) else f"{k}: {v}" for k, v in defaults.items()]
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def skillet_env(tmp_path: Path, monkeypatch):
    """Set up isolated SKILLET_DIR for testing."""
    skillet_dir = tmp_path / ".skillet"
    skillet_dir.mkdir()
    (skillet_dir / "evals").mkdir()

    # Patch SKILLET_DIR in all modules that import it
    import skillet.config
    import skillet.evals.load

    monkeypatch.setattr(skillet.config, "SKILLET_DIR", skillet_dir)
    monkeypatch.setattr(skillet.evals.load, "SKILLET_DIR", skillet_dir)

    return tmp_path


def describe_create_skill():
    """Integration tests for create_skill function."""

    @pytest.mark.asyncio
    async def it_creates_skill_from_valid_evals(skillet_env: Path, mock_claude_query):
        """Happy path: creates SKILL.md from eval files."""
        # Setup evals in SKILLET_DIR/evals/test-skill/
        evals_dir = skillet_env / ".skillet" / "evals" / "test-skill"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")
        _create_eval_file(evals_dir / "002.yaml", prompt="Another prompt")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        # Execute with skill name (not path)
        result = await create_skill("test-skill", output_dir)

        # Assert
        assert result["eval_count"] == 2
        skill_path = result["skill_dir"] / "SKILL.md"
        assert skill_path.exists()

        content = skill_path.read_text()
        assert "---" in content
        assert "test-skill" in content

        # Verify mock was called
        assert mock_claude_query.called
        assert mock_claude_query.call_count == 1

    @pytest.mark.asyncio
    async def it_uses_mock_not_real_api(skillet_env: Path, mock_claude_query):
        """Canary test: verify we're using mocked responses, not real API."""
        evals_dir = skillet_env / ".skillet" / "evals" / "canary-test"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"

        # Set a unique response that would never come from the real API
        unique_marker = "UNIQUE_MOCK_CANARY_RESPONSE_12345"
        mock_claude_query.set_response(f"---\nname: canary\n---\n{unique_marker}")

        result = await create_skill("canary-test", output_dir)

        # If this marker appears, we know the mock is being used
        content = (result["skill_dir"] / "SKILL.md").read_text()
        assert unique_marker in content, "Mock response not found - real API may have been called!"

    @pytest.mark.asyncio
    async def it_works_with_single_eval_file(skillet_env: Path, mock_claude_query):
        """Edge case: works with just one eval."""
        evals_dir = skillet_env / ".skillet" / "evals" / "single-eval"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        result = await create_skill("single-eval", output_dir)

        assert result["eval_count"] == 1
        assert (result["skill_dir"] / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def it_finds_evals_in_nested_directories(skillet_env: Path, mock_claude_query):
        """Edge case: recursively finds YAML files in subdirectories."""
        evals_dir = skillet_env / ".skillet" / "evals" / "nested-evals"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        nested_dir = evals_dir / "subdir"
        nested_dir.mkdir()
        _create_eval_file(nested_dir / "002.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        result = await create_skill("nested-evals", output_dir)

        assert result["eval_count"] == 2

    @pytest.mark.asyncio
    async def it_passes_extra_prompt_to_draft(skillet_env: Path, mock_claude_query):
        """Edge case: extra_prompt is passed through to draft function."""
        evals_dir = skillet_env / ".skillet" / "evals" / "extra-prompt"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        # Execute with extra prompt
        await create_skill("extra-prompt", output_dir, extra_prompt="Be concise")

        # Verify the mock was called (prompt content is tested in unit tests)
        assert mock_claude_query.called

    @pytest.mark.asyncio
    async def it_raises_error_for_empty_evals_directory(skillet_env: Path):
        """Error case: empty evals directory raises EmptyFolderError."""
        evals_dir = skillet_env / ".skillet" / "evals" / "empty-evals"
        evals_dir.mkdir(parents=True)  # Empty directory

        output_dir = skillet_env / "skills"

        with pytest.raises(EmptyFolderError, match="No eval files found"):
            await create_skill("empty-evals", output_dir)

    @pytest.mark.asyncio
    async def it_raises_error_for_nonexistent_evals_directory(skillet_env: Path):
        """Error case: nonexistent evals directory raises EmptyFolderError."""
        output_dir = skillet_env / "skills"

        with pytest.raises(EmptyFolderError, match="No evals found"):
            await create_skill("nonexistent", output_dir)

    @pytest.mark.asyncio
    async def it_raises_error_for_invalid_eval_yaml(skillet_env: Path):
        """Error case: eval missing required fields raises EvalValidationError."""
        evals_dir = skillet_env / ".skillet" / "evals" / "invalid-yaml"
        evals_dir.mkdir(parents=True)

        # Create eval missing 'expected' field
        (evals_dir / "001.yaml").write_text(
            "timestamp: 2025-01-01T00:00:00Z\nprompt: 'Test prompt'\nname: test-skill\n"
        )

        output_dir = skillet_env / "skills"

        with pytest.raises(EvalValidationError, match=r"missing required fields.*expected"):
            await create_skill("invalid-yaml", output_dir)

    @pytest.mark.asyncio
    async def it_raises_error_when_skill_exists_without_overwrite(
        skillet_env: Path, mock_claude_query
    ):
        """Error case: existing skill without overwrite flag raises SkillError."""
        evals_dir = skillet_env / ".skillet" / "evals" / "existing-skill"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        # Create skill first time
        await create_skill("existing-skill", output_dir)

        # Try to create again without overwrite
        with pytest.raises(SkillError, match="Skill already exists"):
            await create_skill("existing-skill", output_dir)

    @pytest.mark.asyncio
    async def it_overwrites_existing_skill_when_flag_set(skillet_env: Path, mock_claude_query):
        """Edge case: overwrite=True replaces existing skill."""
        evals_dir = skillet_env / ".skillet" / "evals" / "overwrite-skill"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_response(VALID_SKILL_RESPONSE)

        # Create skill first time
        result1 = await create_skill("overwrite-skill", output_dir)
        first_content = (result1["skill_dir"] / "SKILL.md").read_text()

        # Create again with overwrite and different response
        mock_claude_query.set_response("---\nname: updated\n---\nUpdated content")
        result2 = await create_skill("overwrite-skill", output_dir, overwrite=True)

        second_content = (result2["skill_dir"] / "SKILL.md").read_text()
        assert second_content != first_content
        assert "Updated content" in second_content

    @pytest.mark.asyncio
    async def it_handles_api_error_gracefully(skillet_env: Path, mock_claude_query):
        """Error case: API error propagates appropriately."""
        evals_dir = skillet_env / ".skillet" / "evals" / "api-error"
        evals_dir.mkdir(parents=True)
        _create_eval_file(evals_dir / "001.yaml")

        output_dir = skillet_env / "skills"
        mock_claude_query.set_error(RuntimeError("API connection failed"))

        with pytest.raises(RuntimeError, match="API connection failed"):
            await create_skill("api-error", output_dir)

        # Verify no partial skill was created
        skill_dir = output_dir / "api-error"
        assert not skill_dir.exists()
