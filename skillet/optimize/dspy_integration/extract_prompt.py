"""Prompt extraction utilities for DSPy integration."""


def extract_prompt(prompt: str | None = None, messages: list[dict] | None = None) -> str:
    """Extract a single prompt string from prompt or messages.

    Args:
        prompt: Simple string prompt
        messages: List of message dicts (OpenAI format)

    Returns:
        Extracted prompt string
    """
    if messages:
        # Extract the last user message as the prompt
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        # Concatenate all messages
        return "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
    return prompt or ""
