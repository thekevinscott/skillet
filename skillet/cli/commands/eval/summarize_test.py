"""Tests for summarize module."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.cli.commands.eval.models import Summary
from skillet.cli.commands.eval.summarize import summarize_responses


def describe_summarize_responses():
    """Tests for summarize_responses function."""

    @pytest.fixture(autouse=True)
    def mock_query_structured():
        with patch(
            "skillet.cli.commands.eval.summarize.query_structured",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = Summary(
                bullets=["Pattern A (50% of responses)", "Pattern B (50% of responses)"]
            )
            yield mock

    @pytest.mark.asyncio
    async def it_returns_formatted_bullets(mock_query_structured):
        results = [
            {"prompt": "test1", "response": "wrong answer 1", "expected": "correct"},
            {"prompt": "test2", "response": "wrong answer 2", "expected": "correct"},
        ]

        summary = await summarize_responses(results)

        assert "- Pattern A" in summary
        assert "- Pattern B" in summary
        mock_query_structured.assert_called_once()

    @pytest.mark.asyncio
    async def it_formats_results_as_yaml(mock_query_structured):
        results = [{"prompt": "test", "response": "answer", "expected": "expected"}]

        await summarize_responses(results)

        # Check that the prompt contains YAML-formatted data
        call_args = mock_query_structured.call_args
        prompt = call_args[0][0]
        assert "Failed Responses" in prompt
        assert "Your Task" in prompt

    @pytest.mark.asyncio
    async def it_handles_empty_results(mock_query_structured):
        mock_query_structured.return_value = Summary(bullets=["No patterns found"])

        results = []

        summary = await summarize_responses(results)

        assert "- No patterns found" in summary
