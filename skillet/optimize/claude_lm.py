"""Custom DSPy LM that uses Claude Agent SDK.

This allows DSPy optimizers to use the same Claude Code environment
that Skillet's eval system uses, ensuring consistent behavior.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any

from dspy.clients.base_lm import BaseLM

from skillet._internal.async_utils import run_sync
from skillet._internal.sdk import query_assistant_text


@dataclass
class Message:
    """OpenAI-style message."""

    role: str
    content: str
    tool_calls: list | None = None


@dataclass
class Choice:
    """OpenAI-style choice."""

    index: int
    message: Message
    finish_reason: str = "stop"
    logprobs: Any = None


@dataclass
class CompletionResponse:
    """OpenAI-style completion response."""

    id: str
    object: str = "chat.completion"
    model: str = "claude-agent-sdk"
    choices: list[Choice] = field(default_factory=list)
    # Usage as dict for DSPy compatibility (it calls dict(response.usage))
    usage: dict = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })


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
        # Convert messages to a single prompt if needed
        if messages:
            # Extract the last user message as the prompt
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                prompt = user_messages[-1].get("content", "")
            else:
                # Concatenate all messages
                prompt = "\n".join(
                    f"{m.get('role', 'user')}: {m.get('content', '')}"
                    for m in messages
                )

        if not prompt:
            prompt = ""

        # Call Claude Agent SDK (synchronously, as DSPy expects sync)
        response_text = run_sync(
            query_assistant_text(
                prompt,
                max_turns=1,
                allowed_tools=[],
                **self.kwargs,
            )
        )

        # Format as OpenAI response object
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

        # Update history for DSPy tracking
        self.update_history(
            {
                "prompt": prompt,
                "response": result,
                "kwargs": kwargs,
            }
        )

        return result

    async def aforward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Async forward pass through Claude Agent SDK."""
        # Convert messages to prompt
        if messages:
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                prompt = user_messages[-1].get("content", "")
            else:
                prompt = "\n".join(
                    f"{m.get('role', 'user')}: {m.get('content', '')}"
                    for m in messages
                )

        if not prompt:
            prompt = ""

        # Call Claude Agent SDK asynchronously
        response_text = await query_assistant_text(
            prompt,
            max_turns=1,
            allowed_tools=[],
            **self.kwargs,
        )

        # Format as OpenAI response object
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

        self.update_history(
            {
                "prompt": prompt,
                "response": result,
                "kwargs": kwargs,
            }
        )

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
