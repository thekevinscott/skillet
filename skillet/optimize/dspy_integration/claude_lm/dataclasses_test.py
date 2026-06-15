"""Tests for the DSPy integration dataclasses."""

from skillet.optimize.dspy_integration.claude_lm.dataclasses import (
    Choice,
    CompletionResponse,
    Message,
    TrialResult,
)


def describe_message():
    def it_defaults_tool_calls_to_none():
        message = Message(role="user", content="hi")
        assert message.role == "user"
        assert message.content == "hi"
        assert message.tool_calls is None


def describe_choice():
    def it_defaults_finish_reason_and_logprobs():
        choice = Choice(index=0, message=Message(role="assistant", content="hi"))
        assert choice.index == 0
        assert choice.message.content == "hi"
        assert choice.finish_reason == "stop"
        assert choice.logprobs is None


def describe_completion_response():
    def it_provides_openai_style_defaults():
        response = CompletionResponse(id="resp-1")
        assert response.object == "chat.completion"
        assert response.model == "claude-agent-sdk"
        assert response.choices == []
        assert response.usage == {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    def it_uses_independent_default_usage_dicts():
        a = CompletionResponse(id="a")
        b = CompletionResponse(id="b")
        a.usage["total_tokens"] = 5
        assert b.usage["total_tokens"] == 0


def describe_trial_result():
    def it_stores_trial_fields():
        trial = TrialResult(
            trial_num=1,
            score=0.5,
            is_best=True,
            instruction="do the thing",
            is_full_eval=False,
        )
        assert trial.trial_num == 1
        assert trial.score == 0.5
        assert trial.is_best is True
        assert trial.instruction == "do the thing"
        assert trial.is_full_eval is False
