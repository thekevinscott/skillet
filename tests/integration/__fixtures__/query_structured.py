"""Mock SDK message sequences for query_structured integration tests.

Each fixture produces the message sequence that claude_agent_sdk.query() would
yield under specific failure conditions observed in production eval_batch runs.
"""

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock


def no_structured_output_messages() -> list:
    """SDK returns text-only response with no StructuredOutput tool call.

    Reproduces: Skill with 19,596 chars (add-gmail) where the model exhausted
    its output budget on text content, never producing the structured output
    tool call. Observed as ValueError("No structured output returned from query").
    """
    return [
        AssistantMessage(
            content=[
                TextBlock(
                    text=(
                        "Here is my analysis of the skill file. "
                        "The skill defines several goals related to Gmail integration..."
                    ),
                )
            ],
            model="claude-sonnet-4-20250514",
        ),
        ResultMessage(
            subtype="result",
            duration_ms=373000,
            duration_api_ms=373000,
            is_error=False,
            num_turns=1,
            session_id="mock-session",
            result=(
                "Here is my analysis of the skill file. "
                "The skill defines several goals related to Gmail integration..."
            ),
            structured_output=None,
        ),
    ]


VALID_CANDIDATES = {
    "candidates": [
        {
            "prompt": "test prompt for voice transcription",
            "expected": "transcribes audio correctly",
            "name": "positive-transcription-basic",
            "category": "positive",
            "domain": "functional",
            "source": "goal:1",
            "confidence": 0.85,
            "rationale": "Tests basic transcription functionality",
        }
    ]
}


def wrapped_structured_output_messages() -> list:
    """SDK returns StructuredOutput with response wrapped in extra `output` key.

    Reproduces: Skill with 13,249 chars (add-voice-transcription) where the LLM
    wrapped its JSON in {"output": {...}} instead of returning the schema directly.
    Observed as ValidationError on GenerateResponse.candidates.
    """
    wrapped_data = {"output": VALID_CANDIDATES}
    return [
        AssistantMessage(
            content=[
                ToolUseBlock(
                    id="tool-wrapped-1",
                    name="StructuredOutput",
                    input=wrapped_data,
                )
            ],
            model="claude-sonnet-4-20250514",
        ),
        ResultMessage(
            subtype="result",
            duration_ms=45000,
            duration_api_ms=45000,
            is_error=False,
            num_turns=1,
            session_id="mock-session",
            result=None,
            structured_output=None,
        ),
    ]
