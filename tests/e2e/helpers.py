import json
from pathlib import Path
from urllib.request import urlopen

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

FIXTURES_DIR = Path(__file__).parent / "__fixtures__"
REPO_ROOT = Path(__file__).parent.parent.parent


class ClaudeResponse:
    """Response from Claude Code with LLM-as-judge matching."""

    def __init__(self, prompt: str, text: str, session_id: str | None = None):
        self.prompt = prompt
        self.text = text
        self.session_id = session_id

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"ClaudeResponse({self.text!r})"

    def __contains__(self, item) -> bool:
        return item in self.text

    async def matches(self, expected: str) -> "MatchResult":
        """Use LLM-as-judge to check if response matches expected behavior."""
        result = await llm_as_judge(self.prompt, self.text, expected)
        return MatchResult(
            passed=result["pass"],
            reasoning=result["reasoning"],
            expected=expected,
            actual=self.text,
        )


class Conversation:
    """Context manager for multi-turn Claude conversations.

    Usage:
        async with Conversation(cwd="/path/to/project") as chat:
            with chat.turn("Write a commit message for this diff"):
                chat.expect_not("conventional commits format")

            with chat.turn("/skillet:gap"):
                chat.expect("expect")  # Should ask what we expected

            with chat.turn("Use conventional commits"):
                chat.expect("saved")  # Should confirm gap saved

            print(chat)  # Print full conversation
    """

    def __init__(self, **options):
        self.options = options
        self.session_id: str | None = None
        self.response: ClaudeResponse | None = None
        self._current_prompt: str | None = None
        self._history: list[tuple[str, str]] = []  # (prompt, response) pairs

    def __str__(self) -> str:
        """Format conversation history like Claude Code output."""
        if not self._history:
            return "(empty conversation)"

        lines = []
        for prompt, response in self._history:
            # User prompt
            lines.append(f"> {prompt}")
            lines.append("")
            # Assistant response - bullet only on non-empty lines
            for line in response.split("\n"):
                if line.strip():
                    lines.append(f"● {line}")
                else:
                    lines.append("")
            lines.append("")

        return "\n".join(lines).strip()

    def __repr__(self) -> str:
        return f"Conversation(turns={len(self._history)}, session_id={self.session_id!r})"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def turn(self, prompt: str):
        """Start a new turn in the conversation."""
        self._current_prompt = prompt
        return _Turn(self, prompt)

    async def _send(self, prompt: str) -> ClaudeResponse:
        """Send a message and store the response."""
        self.response = await claudecode(
            prompt,
            resume=self.session_id,
            **self.options,
        )
        self.session_id = self.response.session_id
        self._history.append((prompt, self.response.text))
        return self.response

    def expect(self, substring: str):
        """Assert the response contains a substring (case-insensitive)."""
        assert self.response is not None, "No response yet - call turn() first"
        assert substring.lower() in self.response.text.lower(), (
            f"Expected response to contain '{substring}'\n"
            f"Prompt: {self._current_prompt}\n"
            f"Response: {self.response.text[:500]}..."
        )

    def expect_not(self, substring: str):
        """Assert the response does NOT contain a substring (case-insensitive)."""
        assert self.response is not None, "No response yet - call turn() first"
        assert substring.lower() not in self.response.text.lower(), (
            f"Expected response NOT to contain '{substring}'\n"
            f"Prompt: {self._current_prompt}\n"
            f"Response: {self.response.text[:500]}..."
        )

    async def expect_matches(self, expected: str):
        """Use LLM-as-judge to verify response matches expected behavior."""
        assert self.response is not None, "No response yet - call turn() first"
        result = await self.response.matches(expected)
        assert result, (
            f"Response did not match expectation\n"
            f"Prompt: {self._current_prompt}\n"
            f"Expected: {expected}\n"
            f"Actual: {self.response.text[:300]}...\n"
            f"Reasoning: {result.reasoning}"
        )

    async def expect_not_matches(self, expected: str):
        """Use LLM-as-judge to verify response does NOT match expected behavior."""
        assert self.response is not None, "No response yet - call turn() first"
        result = await self.response.matches(expected)
        assert not result, (
            f"Response unexpectedly matched expectation\n"
            f"Prompt: {self._current_prompt}\n"
            f"Did not expect: {expected}\n"
            f"Actual: {self.response.text[:300]}..."
        )


class _Turn:
    """Context manager for a single turn in a conversation."""

    def __init__(self, conversation: Conversation, prompt: str):
        self.conversation = conversation
        self.prompt = prompt

    async def __aenter__(self):
        await self.conversation._send(self.prompt)
        return self.conversation

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MatchResult:
    """Result of LLM-as-judge comparison with assertion-friendly output."""

    def __init__(self, passed: bool, reasoning: str, expected: str, actual: str):
        self.passed = passed
        self.reasoning = reasoning
        self.expected = expected
        self.actual = actual

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        if self.passed:
            return "MatchResult(passed=True)"
        return (
            f"MatchResult(passed=False)\n"
            f"  Expected: {self.expected}\n"
            f"  Actual: {self.actual[:200]}{'...' if len(self.actual) > 200 else ''}\n"
            f"  Reasoning: {self.reasoning}"
        )


async def claudecode(
    prompt: str, resume: str | None = None, debug: bool = False, **options
) -> ClaudeResponse:
    """Run Claude Code with a prompt and return the response.

    Args:
        prompt: The prompt to send
        resume: Session ID to resume (for multi-turn conversations)
        debug: If True, print debug messages
        **options: Additional options passed to ClaudeAgentOptions
    """
    text, session_id = await query_assistant_text(prompt, resume=resume, debug=debug, **options)
    return ClaudeResponse(prompt, text, session_id)


async def query_assistant_text(
    prompt: str, resume: str | None = None, debug: bool = False, **options
) -> tuple[str, str | None]:
    """Query Claude and return the assistant's text response and session ID."""
    # Allow SlashCommand tool for slash command testing
    # Load settings from project to pick up .claude/commands/
    opts = ClaudeAgentOptions(
        max_turns=10, allowed_tools=["SlashCommand"], setting_sources=["project"], **options
    )
    if resume:
        opts.resume = resume

    result = ""
    session_id = None

    async for message in query(prompt=prompt, options=opts):
        if debug:
            print(f"[DEBUG] message type: {type(message).__name__}, message: {message}")

        # Capture session ID from init message
        if hasattr(message, "subtype") and message.subtype == "init":
            if hasattr(message, "session_id"):
                session_id = message.session_id
            elif hasattr(message, "data") and isinstance(message.data, dict):
                session_id = message.data.get("session_id")

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text

    return result.strip(), session_id


async def llm_as_judge(prompt: str, response: str, expected: str) -> dict:
    """Use LLM-as-judge to evaluate if a response meets expectations.

    Returns:
        dict with 'pass' (bool) and 'reasoning' (str)
    """
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

{{
    "pass": boolean,
    "reasoning": one sentence explanation,
}}
"""

    result, _ = await query_assistant_text(judge_prompt)
    return json.loads(result)


def add_evals(skillet_env: Path, name: str, count: int = 0) -> Path:
    """Create an eval folder with optional existing evals.

    Args:
        skillet_env: The skillet_env fixture path
        name: Eval category name (e.g., "conventional-commits")
        count: Number of existing eval files to create

    Returns:
        Path to the created folder
    """
    folder = skillet_env / ".skillet" / "evals" / name
    folder.mkdir(parents=True, exist_ok=True)

    for i in range(1, count + 1):
        eval_file = folder / f"{i:03d}.yaml"
        eval_file.write_text(
            f"timestamp: 2025-01-01T00:00:00Z\n"
            f"prompt: 'Test prompt {i}'\n"
            f"actual: 'Test actual {i}'\n"
            f"expected: 'Test expected {i}'\n"
            f"name: {name}\n"
        )

    return folder


def list_evals(skillet_env: Path, name: str) -> list[Path]:
    """List all eval files in a category.

    Args:
        skillet_env: The skillet_env fixture path
        name: Eval category name

    Returns:
        Sorted list of eval file paths
    """
    folder = skillet_env / ".skillet" / "evals" / name
    if not folder.exists():
        return []
    return sorted(folder.glob("*.yaml"))


def get_github_diff(commit_url: str) -> str:
    """Fetch a diff from GitHub, caching to fixtures.

    Args:
        commit_url: GitHub commit URL (e.g., https://github.com/pallets/click/commit/abc123)

    Returns:
        The diff content as a string

    Caches to: __fixtures__/<org>/<repo>/<commit_sha>.diff
    """
    # Parse URL: https://github.com/org/repo/commit/sha
    parts = commit_url.rstrip("/").split("/")
    org = parts[-4]
    repo = parts[-3]
    sha = parts[-1]

    cache_file = FIXTURES_DIR / org / repo / f"{sha}.diff"

    # Return cached if available
    if cache_file.exists():
        return cache_file.read_text()

    # Fetch from GitHub
    patch_url = f"{commit_url}.patch"
    with urlopen(patch_url) as response:
        diff = response.read().decode("utf-8")

    # Cache it
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(diff)

    return diff
