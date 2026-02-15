"""Tests for claude_lm/for_query module."""

from unittest.mock import MagicMock, patch

import pytest

from skillet.optimize.dspy_integration.claude_lm.for_query import for_query


def describe_for_query():
    @pytest.mark.asyncio
    async def it_yields_blocks_from_messages():
        mock_block = MagicMock()
        mock_block.text = "hello"
        mock_message = MagicMock()
        mock_message.content = [mock_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.claude_lm.for_query.query", mock_query_gen):
            blocks = []
            async for block in for_query("test prompt"):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "hello"

    @pytest.mark.asyncio
    async def it_filters_by_block_type():
        from claude_agent_sdk import TextBlock, ToolUseBlock

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "text content"

        mock_tool_block = MagicMock(spec=ToolUseBlock)
        mock_tool_block.name = "bash"

        mock_message = MagicMock()
        mock_message.content = [mock_text_block, mock_tool_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.claude_lm.for_query.query", mock_query_gen):
            blocks = []
            async for block in for_query("test", block_type=TextBlock):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "text content"

    @pytest.mark.asyncio
    async def it_skips_messages_without_content():
        mock_message = MagicMock(spec=[])
        del mock_message.content

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.claude_lm.for_query.query", mock_query_gen):
            blocks = []
            async for block in for_query("test"):
                blocks.append(block)

            assert len(blocks) == 0
