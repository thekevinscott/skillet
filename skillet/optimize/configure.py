"""DSPy configuration for Skillet."""

import dspy

from .claude_lm import ClaudeAgentLM


def configure_dspy() -> ClaudeAgentLM:
    """Configure DSPy to use Claude Agent SDK.

    This uses a custom LM that wraps Claude Agent SDK, ensuring:
    - Same authentication as the Claude CLI
    - Consistent behavior with Skillet's eval system
    - No need for ANTHROPIC_API_KEY

    Returns:
        Configured ClaudeAgentLM instance

    Example:
        from skillet.optimize import configure_dspy

        configure_dspy()
        # Now DSPy uses Claude Agent SDK for all LLM calls
    """
    lm = ClaudeAgentLM()
    dspy.configure(lm=lm)
    return lm
