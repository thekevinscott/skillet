"""Tests for ClaudeAgentLM."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.optimize.dspy_integration.claude_lm import ClaudeAgentLM


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
        @patch("skillet.optimize.dspy_integration.claude_lm.run_sync")
        def it_calls_query_assistant_text(mock_run_sync):
            mock_run_sync.return_value = "Hello world"
            lm = ClaudeAgentLM()
            result = lm.forward(prompt="Test prompt")
            assert mock_run_sync.called
            assert len(result.choices) == 1
            assert result.choices[0].message.content == "Hello world"

        @patch("skillet.optimize.dspy_integration.claude_lm.run_sync")
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

        @patch("skillet.optimize.dspy_integration.claude_lm.run_sync")
        def it_updates_history(mock_run_sync):
            mock_run_sync.return_value = "Answer"
            lm = ClaudeAgentLM()
            lm.forward(prompt="Question")
            assert len(lm.history) == 1
            assert lm.history[0]["prompt"] == "Question"

        @patch("skillet.optimize.dspy_integration.claude_lm.run_sync")
        def it_handles_empty_prompt(mock_run_sync):
            mock_run_sync.return_value = ""
            lm = ClaudeAgentLM()
            result = lm.forward()
            assert result.choices[0].message.content == ""

    def describe_aforward():
        CLAUDE_LM_QUERY = "skillet.optimize.dspy_integration.claude_lm.query_assistant_text"

        @pytest.mark.asyncio
        @patch(CLAUDE_LM_QUERY, new_callable=AsyncMock)
        async def it_calls_query_assistant_text_async(mock_query):
            mock_query.return_value = "Async response"
            lm = ClaudeAgentLM()
            result = await lm.aforward(prompt="Async test")
            assert result.choices[0].message.content == "Async response"

        @pytest.mark.asyncio
        @patch(CLAUDE_LM_QUERY, new_callable=AsyncMock)
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
        @patch("skillet.optimize.dspy_integration.claude_lm.run_sync")
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
