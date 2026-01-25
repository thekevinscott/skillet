"""Tests for query_text module."""

from unittest.mock import MagicMock, patch

import pytest

from skillet.optimize.dspy_integration.query_text import for_query, query_assistant_text


def describe_for_query():
    """Tests for for_query async generator."""

    @pytest.mark.asyncio
    async def it_yields_blocks_from_messages():
        """Test that for_query yields content blocks from messages."""
        mock_block = MagicMock()
        mock_block.text = "hello"
        mock_message = MagicMock()
        mock_message.content = [mock_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.query_text.query", mock_query_gen):
            blocks = []
            async for block in for_query("test prompt"):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "hello"

    @pytest.mark.asyncio
    async def it_filters_by_block_type():
        """Test that block_type parameter filters blocks."""
        from claude_agent_sdk import TextBlock, ToolUseBlock

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "text content"

        mock_tool_block = MagicMock(spec=ToolUseBlock)
        mock_tool_block.name = "bash"

        mock_message = MagicMock()
        mock_message.content = [mock_text_block, mock_tool_block]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.query_text.query", mock_query_gen):
            blocks = []
            async for block in for_query("test", block_type=TextBlock):
                blocks.append(block)

            assert len(blocks) == 1
            assert blocks[0].text == "text content"

    @pytest.mark.asyncio
    async def it_skips_messages_without_content():
        """Test that messages without content attribute are skipped."""
        mock_message = MagicMock(spec=[])
        del mock_message.content

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.query_text.query", mock_query_gen):
            blocks = []
            async for block in for_query("test"):
                blocks.append(block)

            assert len(blocks) == 0


def describe_query_assistant_text():
    """Tests for query_assistant_text function."""

    @pytest.mark.asyncio
    async def it_returns_concatenated_text():
        """Test that text blocks are concatenated."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text1 = MagicMock(spec=TextBlock)
        mock_text1.text = "Hello "
        mock_text2 = MagicMock(spec=TextBlock)
        mock_text2.text = "World"

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text1, mock_text2]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.query_text.query", mock_query_gen):
            result = await query_assistant_text("test prompt")

            assert result == "Hello World"

    @pytest.mark.asyncio
    async def it_strips_whitespace():
        """Test that result is stripped."""
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "  response  "

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("skillet.optimize.dspy_integration.query_text.query", mock_query_gen):
            result = await query_assistant_text("test")

            assert result == "response"
