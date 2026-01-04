"""DSPy configuration for Skillet."""

from .claude_lm import ClaudeAgentLM


def get_claude_lm() -> ClaudeAgentLM:
    """Get a ClaudeAgentLM instance for use with DSPy.

    Returns a custom LM that wraps Claude Agent SDK, ensuring:
    - Same authentication as the Claude CLI
    - Consistent behavior with Skillet's eval system
    - No need for ANTHROPIC_API_KEY

    Use with dspy.context() to avoid global side effects:

        import dspy
        from skillet.optimize import get_claude_lm

        with dspy.context(lm=get_claude_lm()):
            # DSPy calls here use Claude Agent SDK
            optimized = optimizer.compile(module, trainset=data)

    Returns:
        ClaudeAgentLM instance
    """
    return ClaudeAgentLM()
