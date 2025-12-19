"""Tests for summarize module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.commands.eval.summarize import summarize_responses


def describe_summarize_responses():
    """Tests for summarize_responses function."""

    @pytest.mark.asyncio
    async def it_returns_summary_from_llm():
        with patch(
            "skillet.cli.commands.eval.summarize.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = (
                "- Pattern A (50% of responses)\n- Pattern B (50% of responses)"
            )

            results = [
                {"prompt": "test1", "response": "wrong answer 1", "expected": "correct"},
                {"prompt": "test2", "response": "wrong answer 2", "expected": "correct"},
            ]

            summary = await summarize_responses(results)

            assert "Pattern A" in summary
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def it_formats_results_as_yaml():
        with patch(
            "skillet.cli.commands.eval.summarize.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "Summary"

            results = [{"prompt": "test", "response": "answer", "expected": "expected"}]

            await summarize_responses(results)

            # Check that the prompt contains YAML-formatted data
            call_args = mock_query.call_args
            prompt = call_args[0][0]
            assert "Failed Responses" in prompt
            assert "Your Task" in prompt

    @pytest.mark.asyncio
    async def it_handles_empty_results():
        with patch(
            "skillet.cli.commands.eval.summarize.query_assistant_text",
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = "No patterns found"

            results = []

            summary = await summarize_responses(results)

            assert summary == "No patterns found"
