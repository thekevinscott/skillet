"""Dataclasses for DSPy integration."""

from dataclasses import dataclass, field
from typing import Any


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
    usage: dict = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )


@dataclass
class TrialResult:
    """Result of a single optimization trial."""

    trial_num: int
    score: float
    is_best: bool
    instruction: str
    is_full_eval: bool
