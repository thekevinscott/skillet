"""Tests for skill/draft module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.skill.draft import draft_skill
from skillet.skill.models import SkillContent


def describe_draft_skill():
    """Tests for draft_skill function."""

    @pytest.fixture(autouse=True)
    def mock_query_structured():
        with patch(
            "skillet.skill.draft.query_structured",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = SkillContent(content="# Generated Skill")
            yield mock

    @pytest.mark.asyncio
    async def it_calls_claude_with_evals_summary(mock_query_structured):
        evals = [
            {"prompt": "Say hello", "expected": "Respond with greeting"},
            {"prompt": "Count to 5", "expected": "1, 2, 3, 4, 5"},
        ]

        result = await draft_skill("test-skill", evals)

        assert result == "# Generated Skill"
        mock_query_structured.assert_called_once()

        # Check that evals were included in the prompt
        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "test-skill" in prompt
        assert "Say hello" in prompt
        assert "Count to 5" in prompt

    @pytest.mark.asyncio
    async def it_includes_extra_prompt_when_provided(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Skill")

        evals = [{"prompt": "test", "expected": "result"}]

        await draft_skill("my-skill", evals, extra_prompt="Be very concise")

        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "Be very concise" in prompt

    @pytest.mark.asyncio
    async def it_extracts_content_from_structured_output(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Skill Content")

        evals = [{"prompt": "p", "expected": "e"}]

        result = await draft_skill("test", evals)

        assert result == "# Skill Content"

    @pytest.mark.asyncio
    async def it_handles_empty_evals_list(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Empty Skill")

        result = await draft_skill("empty", [])

        assert result == "# Empty Skill"

    @pytest.mark.asyncio
    async def it_formats_multiple_evals_with_numbers(mock_query_structured):
        mock_query_structured.return_value = SkillContent(content="# Result")

        evals = [
            {"prompt": "first", "expected": "one"},
            {"prompt": "second", "expected": "two"},
            {"prompt": "third", "expected": "three"},
        ]

        await draft_skill("numbered", evals)

        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "Eval 1" in prompt
        assert "Eval 2" in prompt
        assert "Eval 3" in prompt
