"""Tests for the DSPy configuration factory."""

from unittest.mock import patch

from skillet.optimize.dspy_integration.claude_lm.configure import get_claude_lm

_MODULE = "skillet.optimize.dspy_integration.claude_lm.configure"


def describe_get_claude_lm():
    def it_returns_a_claude_agent_lm_instance():
        with patch(f"{_MODULE}.ClaudeAgentLM") as mock_lm:
            result = get_claude_lm()

            mock_lm.assert_called_once_with()
            assert result is mock_lm.return_value
