"""LLM-as-judge for evaluating responses against expected behavior."""


async def judge_response(prompt: str, response: str, expected: str) -> dict:
    """Use Claude as a judge to evaluate if a response meets expectations.

    Args:
        prompt: The original user prompt
        response: Claude's response to evaluate
        expected: What the user expected (from the gap file)

    Returns:
        dict with 'pass' (bool) and 'reasoning' (str)
    """
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    judge_prompt = f"""You are evaluating whether an AI response meets the user's expectations.

## Original Prompt
{prompt}

## AI Response
{response}

## Expected Behavior
{expected}

## Your Task
Determine if the AI response meets the expected behavior. Be strict but fair.

Respond in this exact format:
PASS: yes or no
REASONING: one sentence explanation
"""

    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
    )

    result = ""
    async for message in query(prompt=judge_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text

    # Parse the response
    lines = result.strip().split("\n")
    pass_line = lines[0] if lines else ""
    reasoning_line = lines[1] if len(lines) > 1 else ""

    passed = "yes" in pass_line.lower()
    reasoning = reasoning_line.replace("REASONING:", "").strip()

    return {
        "pass": passed,
        "reasoning": reasoning,
        "raw": result,
    }
