"""Custom DSPy LM that uses Claude Agent SDK.

This allows DSPy optimizers to use the same Claude Code environment
that Skillet's eval system uses, ensuring consistent behavior.
"""

import uuid
from typing import Any

from dspy.clients.base_lm import BaseLM

from skillet._internal.async_utils import run_sync
from skillet._internal.sdk import query_assistant_text

from .dataclasses import Choice, CompletionResponse, Message
from .extract_prompt import extract_prompt


class ClaudeAgentLM(BaseLM):
    """DSPy LM that wraps Claude Agent SDK.

    This allows DSPy to use Claude Code's environment, including:
    - Same authentication as the Claude CLI
    - Access to tools and slash commands
    - Consistent behavior with Skillet's eval system

    Example:
        import dspy
        from skillet.optimize import ClaudeAgentLM

        lm = ClaudeAgentLM()
        dspy.configure(lm=lm)

        # Now DSPy will use Claude Agent SDK for all LLM calls
        predict = dspy.Predict("question -> answer")
        result = predict(question="What is 2+2?")
    """

    def __init__(
        self,
        model: str = "claude-agent-sdk",
        model_type: str = "chat",
        max_tokens: int = 4096,
        **kwargs,
    ):
        """Initialize the Claude Agent LM.

        Args:
            model: Model identifier (for DSPy tracking, actual model is determined by Claude CLI)
            model_type: Type of model interface (chat, text, responses)
            max_tokens: Maximum tokens for response
            **kwargs: Additional options passed to Claude Agent SDK
        """
        self.model = model
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self.history: list[dict] = []

    def forward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Run a forward pass through Claude Agent SDK.

        Args:
            prompt: Simple string prompt
            messages: List of message dicts (OpenAI format)
            **kwargs: Additional options

        Returns:
            CompletionResponse in OpenAI format
        """
        extracted_prompt = extract_prompt(prompt, messages)

        # Call Claude Agent SDK (synchronously, as DSPy expects sync)
        response_text = run_sync(
            query_assistant_text(
                extracted_prompt,
                max_turns=1,
                allowed_tools=[],
                **self.kwargs,
            )
        )

        return self._build_response(extracted_prompt, response_text, kwargs)

    async def aforward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Async forward pass through Claude Agent SDK."""
        extracted_prompt = extract_prompt(prompt, messages)

        # Call Claude Agent SDK asynchronously
        response_text = await query_assistant_text(
            extracted_prompt,
            max_turns=1,
            allowed_tools=[],
            **self.kwargs,
        )

        return self._build_response(extracted_prompt, response_text, kwargs)

    def _build_response(self, prompt: str, response_text: str, kwargs: dict) -> CompletionResponse:
        """Build a CompletionResponse and update history."""
        result = CompletionResponse(
            id=f"claude-agent-{uuid.uuid4().hex[:8]}",
            model=self.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=response_text),
                )
            ],
        )

        self.update_history({"prompt": prompt, "response": result, "kwargs": kwargs})

        return result

    def copy(self, **kwargs) -> "ClaudeAgentLM":
        """Return a copy of this LM with updated kwargs."""
        new_kwargs = {**self.kwargs, **kwargs}
        return ClaudeAgentLM(
            model=self.model,
            model_type=self.model_type,
            max_tokens=self.max_tokens,
            **new_kwargs,
        )

    def update_history(self, entry: dict[str, Any]) -> None:
        """Update the history with a new entry."""
        self.history.append(entry)

    def inspect_history(self, n: int = 1) -> list[dict]:
        """Return the last n history entries."""
        return self.history[-n:]
