"""Tests for ClaudeAgentLM."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.optimize.claude_lm import (
    Choice,
    ClaudeAgentLM,
    CompletionResponse,
    Message,
)


def describe_Message():
    def it_stores_role_and_content():
        msg = Message(role="assistant", content="Hello")
        assert msg.role == "assistant"
        assert msg.content == "Hello"
        assert msg.tool_calls is None

    def it_allows_tool_calls():
        msg = Message(role="assistant", content="", tool_calls=[{"id": "1"}])
        assert msg.tool_calls == [{"id": "1"}]


def describe_Choice():
    def it_stores_message():
        msg = Message(role="assistant", content="test")
        choice = Choice(index=0, message=msg)
        assert choice.index == 0
        assert choice.message == msg
        assert choice.finish_reason == "stop"


def describe_CompletionResponse():
    def it_creates_with_defaults():
        response = CompletionResponse(id="test-123")
        assert response.id == "test-123"
        assert response.object == "chat.completion"
        assert response.model == "claude-agent-sdk"
        assert response.choices == []
        assert response.usage == {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }


def describe_ClaudeAgentLM():
    def describe_init():
        def it_sets_default_values():
            lm = ClaudeAgentLM()
            assert lm.model == "claude-agent-sdk"
            assert lm.model_type == "chat"
            assert lm.max_tokens == 4096
            assert lm.history == []

        def it_accepts_custom_values():
            lm = ClaudeAgentLM(model="custom", max_tokens=2048, custom_arg="value")
            assert lm.model == "custom"
            assert lm.max_tokens == 2048
            assert lm.kwargs["custom_arg"] == "value"

    def describe_forward():
        @patch("skillet.optimize.claude_lm.run_sync")
        def it_calls_query_assistant_text(mock_run_sync):
            mock_run_sync.return_value = "Hello world"
            lm = ClaudeAgentLM()
            result = lm.forward(prompt="Test prompt")
            assert mock_run_sync.called
            assert len(result.choices) == 1
            assert result.choices[0].message.content == "Hello world"

        @patch("skillet.optimize.claude_lm.run_sync")
        def it_extracts_prompt_from_messages(mock_run_sync):
            mock_run_sync.return_value = "Response"
            lm = ClaudeAgentLM()
            result = lm.forward(
                messages=[
                    {"role": "system", "content": "System prompt"},
                    {"role": "user", "content": "User question"},
                ]
            )
            assert result.choices[0].message.content == "Response"

        @patch("skillet.optimize.claude_lm.run_sync")
        def it_updates_history(mock_run_sync):
            mock_run_sync.return_value = "Answer"
            lm = ClaudeAgentLM()
            lm.forward(prompt="Question")
            assert len(lm.history) == 1
            assert lm.history[0]["prompt"] == "Question"

        @patch("skillet.optimize.claude_lm.run_sync")
        def it_handles_empty_prompt(mock_run_sync):
            mock_run_sync.return_value = ""
            lm = ClaudeAgentLM()
            result = lm.forward()
            assert result.choices[0].message.content == ""

    def describe_aforward():
        @pytest.mark.asyncio
        @patch("skillet.optimize.claude_lm.query_assistant_text", new_callable=AsyncMock)
        async def it_calls_query_assistant_text_async(mock_query):
            mock_query.return_value = "Async response"
            lm = ClaudeAgentLM()
            result = await lm.aforward(prompt="Async test")
            assert result.choices[0].message.content == "Async response"

        @pytest.mark.asyncio
        @patch("skillet.optimize.claude_lm.query_assistant_text", new_callable=AsyncMock)
        async def it_extracts_prompt_from_messages_async(mock_query):
            mock_query.return_value = "Response"
            lm = ClaudeAgentLM()
            result = await lm.aforward(
                messages=[{"role": "user", "content": "Question"}]
            )
            assert result.choices[0].message.content == "Response"

    def describe_copy():
        def it_returns_new_instance():
            lm = ClaudeAgentLM(max_tokens=1000)
            copied = lm.copy(extra_arg="new")
            assert copied is not lm
            assert copied.max_tokens == 1000
            assert copied.kwargs["extra_arg"] == "new"

        def it_preserves_original():
            lm = ClaudeAgentLM()
            lm.copy(extra_arg="test")
            assert "extra_arg" not in lm.kwargs

    def describe_inspect_history():
        @patch("skillet.optimize.claude_lm.run_sync")
        def it_returns_last_n_entries(mock_run_sync):
            mock_run_sync.return_value = "Response"
            lm = ClaudeAgentLM()
            lm.forward(prompt="First")
            lm.forward(prompt="Second")
            lm.forward(prompt="Third")
            history = lm.inspect_history(n=2)
            assert len(history) == 2
            assert history[0]["prompt"] == "Second"
            assert history[1]["prompt"] == "Third"
