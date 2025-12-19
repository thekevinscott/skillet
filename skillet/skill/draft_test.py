"""Tests for skill/draft module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.skill.draft import draft_skill


def describe_draft_skill():
    """Tests for draft_skill function."""

    @pytest.mark.asyncio
    async def it_calls_claude_with_gaps_summary():
        with patch(
            "skillet.skill.draft.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "# Generated Skill"

            gaps = [
                {"prompt": "Say hello", "expected": "Respond with greeting"},
                {"prompt": "Count to 5", "expected": "1, 2, 3, 4, 5"},
            ]

            result = await draft_skill("test-skill", gaps)

            assert result == "# Generated Skill"
            mock_query.assert_called_once()

            # Check that gaps were included in the prompt
            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "test-skill" in prompt
            assert "Say hello" in prompt
            assert "Count to 5" in prompt

    @pytest.mark.asyncio
    async def it_includes_extra_prompt_when_provided():
        with patch(
            "skillet.skill.draft.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "# Skill"

            gaps = [{"prompt": "test", "expected": "result"}]

            await draft_skill("my-skill", gaps, extra_prompt="Be very concise")

            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "Be very concise" in prompt

    @pytest.mark.asyncio
    async def it_strips_markdown_from_response():
        with patch(
            "skillet.skill.draft.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "```markdown\n# Skill Content\n```"

            gaps = [{"prompt": "p", "expected": "e"}]

            result = await draft_skill("test", gaps)

            assert result == "# Skill Content"
            assert "```" not in result

    @pytest.mark.asyncio
    async def it_handles_empty_gaps_list():
        with patch(
            "skillet.skill.draft.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "# Empty Skill"

            result = await draft_skill("empty", [])

            assert result == "# Empty Skill"

    @pytest.mark.asyncio
    async def it_formats_multiple_gaps_with_numbers():
        with patch(
            "skillet.skill.draft.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "# Result"

            gaps = [
                {"prompt": "first", "expected": "one"},
                {"prompt": "second", "expected": "two"},
                {"prompt": "third", "expected": "three"},
            ]

            await draft_skill("numbered", gaps)

            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "Gap 1" in prompt
            assert "Gap 2" in prompt
            assert "Gap 3" in prompt
