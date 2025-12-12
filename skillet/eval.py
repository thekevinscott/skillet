"""Evaluate Claude against captured gaps, with or without a skill."""

import asyncio
import contextlib
import sys
from pathlib import Path

import yaml

from skillet.cache import (
    gap_cache_key,
    get_cache_dir,
    get_cached_iterations,
    save_iteration,
)
from skillet.judge import judge_response

SKILLET_DIR = Path.home() / ".skillet"

# Status symbols
PENDING = "○"
CACHED = "●"
PASS = "✓"
FAIL = "✗"

# Spinner frames for running state
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class LiveDisplay:
    """Live updating display for parallel eval runs."""

    def __init__(self, tasks: list[dict]):
        """Initialize with list of tasks.

        Each task dict has: gap_source, gap_idx, iteration, total_iterations
        """
        self.tasks = tasks
        self.status = {self._key(t): {"state": "pending", "result": None} for t in tasks}
        self.lock = asyncio.Lock()
        self.spinner_task = None
        self.running = False

    def _key(self, task: dict) -> str:
        return f"{task['gap_idx']}:{task['iteration']}"

    async def start(self):
        """Start the spinner animation loop."""
        self.running = True
        self.spinner_task = asyncio.create_task(self._spin())

    async def stop(self):
        """Stop the spinner animation loop."""
        self.running = False
        if self.spinner_task:
            self.spinner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.spinner_task

    async def _spin(self):
        """Animation loop for spinners."""
        frame_idx = 0
        while self.running:
            async with self.lock:
                self._render(frame_idx)
            frame_idx = (frame_idx + 1) % len(SPINNER_FRAMES)
            await asyncio.sleep(0.08)

    async def update(self, task: dict, state: str, result: dict | None = None):
        async with self.lock:
            key = self._key(task)
            self.status[key] = {"state": state, "result": result}

    def _render(self, frame_idx: int = 0):
        """Render current status to stderr."""
        # Group by gap
        gaps = {}
        for task in self.tasks:
            gap_idx = task["gap_idx"]
            if gap_idx not in gaps:
                gaps[gap_idx] = {"source": task["gap_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            gaps[gap_idx]["iterations"].append(status)

        # Build output
        lines = []
        for gap_idx in sorted(gaps.keys()):
            gap = gaps[gap_idx]
            iterations = gap["iterations"]

            # Build iteration symbols
            symbols = []
            for it in iterations:
                if it["state"] == "pending":
                    symbols.append(PENDING)
                elif it["state"] == "cached":
                    symbols.append(CACHED)
                elif it["state"] == "running":
                    symbols.append(SPINNER_FRAMES[frame_idx])
                elif it["state"] == "done":
                    if it["result"] and it["result"].get("pass"):
                        symbols.append(PASS)
                    else:
                        symbols.append(FAIL)

            line = f"  {gap['source']}: {' '.join(symbols)}"
            lines.append(line)

        # Clear and redraw
        output = "\r\033[K" + "\n\033[K".join(lines)
        # Move cursor back up
        if len(lines) > 1:
            output += f"\033[{len(lines) - 1}A\r"

        sys.stderr.write(output)
        sys.stderr.flush()

    def finalize(self):
        """Print final state without cursor manipulation."""
        gaps = {}
        for task in self.tasks:
            gap_idx = task["gap_idx"]
            if gap_idx not in gaps:
                gaps[gap_idx] = {"source": task["gap_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            gaps[gap_idx]["iterations"].append(status)

        # Move to end and print final state
        sys.stderr.write("\n" * len(gaps))
        sys.stderr.write("\r")

        for gap_idx in sorted(gaps.keys()):
            gap = gaps[gap_idx]
            iterations = gap["iterations"]

            symbols = []
            pass_count = 0
            for it in iterations:
                if it["state"] in ("done", "cached"):
                    if it["result"] and it["result"].get("pass"):
                        symbols.append(PASS)
                        pass_count += 1
                    else:
                        symbols.append(FAIL)
                else:
                    symbols.append(PENDING)

            pct = pass_count / len(iterations) * 100 if iterations else 0
            line = f"  {gap['source']}: {' '.join(symbols)} ({pct:.0f}%)\n"
            sys.stderr.write(line)

        sys.stderr.flush()


class EvalError(Exception):
    """Error during evaluation."""


def load_gaps(name: str) -> list[dict]:
    """Load all gap files for a skill from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts with _source and _content fields
    """
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise EvalError(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise EvalError(f"Not a directory: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        content = gap_file.read_text()
        gap = yaml.safe_load(content)
        gap["_source"] = gap_file.name
        gap["_content"] = content
        gaps.append(gap)

    if not gaps:
        raise EvalError(f"No gap files found in {gaps_dir}")

    return gaps


async def run_prompt(
    prompt: str,
    skill_path: Path | None = None,
    allowed_tools: list[str] | None = None,
) -> str:
    """Run a prompt through Claude and return the response."""
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    # If skill path provided, set cwd to parent of .claude/skills so SDK discovers it
    # e.g., skill_path=/tmp/proj/.claude/skills/browser-fallback -> cwd=/tmp/proj
    cwd = None
    # skill_path is like /path/to/.claude/skills/skill-name
    # We need cwd to be /path/to (parent of .claude)
    if skill_path and ".claude" in skill_path.parts:
        claude_idx = skill_path.parts.index(".claude")
        cwd = str(Path(*skill_path.parts[:claude_idx]))

    # Build allowed_tools, ensuring Skill is included if we have a skill
    tools: list[str]
    if skill_path:
        if allowed_tools is not None and "Skill" not in allowed_tools:
            tools = ["Skill", *list(allowed_tools)]
        elif allowed_tools is None:
            tools = ["Skill", "Bash", "Read", "Write", "WebFetch"]
        else:
            tools = list(allowed_tools)
    else:
        tools = list(allowed_tools) if allowed_tools else []

    options = ClaudeAgentOptions(
        max_turns=3,
        allowed_tools=tools if tools else None,  # type: ignore[arg-type]
        cwd=cwd,
        setting_sources=["project"] if cwd else None,
    )

    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    if not response_text:
        response_text = "(no text response - Claude may have only used tools)"

    return response_text


async def run_single_eval(
    task: dict,
    name: str,
    skill_path: Path | None,
    allowed_tools: list[str] | None,
    display: LiveDisplay,
) -> dict:
    """Run a single evaluation task, using cache if available."""
    # Check cache first
    gap_key = gap_cache_key(task["gap_source"], task["gap_content"])
    cache_dir = get_cache_dir(name, gap_key, skill_path)
    cached = get_cached_iterations(cache_dir)

    # If we have this iteration cached, use it
    if len(cached) >= task["iteration"]:
        result = cached[task["iteration"] - 1]
        result["gap_idx"] = task["gap_idx"]
        result["gap_source"] = task["gap_source"]
        result["cached"] = True
        await display.update(task, "cached", result)
        return result

    # Otherwise, run it
    await display.update(task, "running")

    try:
        response = await run_prompt(task["prompt"], skill_path, allowed_tools)
        judgment = await judge_response(
            prompt=task["prompt"],
            response=response,
            expected=task["expected"],
        )

        result = {
            "gap_idx": task["gap_idx"],
            "gap_source": task["gap_source"],
            "iteration": task["iteration"],
            "response": response,
            "judgment": judgment,
            "pass": judgment["pass"],
            "cached": False,
        }

        # Save to cache
        save_iteration(
            cache_dir,
            task["iteration"],
            {
                "iteration": task["iteration"],
                "response": response,
                "judgment": judgment,
                "pass": judgment["pass"],
            },
        )

        await display.update(task, "done", result)
        return result
    except Exception as e:
        result = {
            "gap_idx": task["gap_idx"],
            "gap_source": task["gap_source"],
            "iteration": task["iteration"],
            "response": str(e),
            "judgment": {"pass": False, "reasoning": f"Error: {e}"},
            "pass": False,
            "cached": False,
        }
        await display.update(task, "done", result)
        return result


async def run_eval(
    name: str,
    skill_path: Path | None = None,
    samples: int = 3,
    max_gaps: int | None = None,
    allowed_tools: list[str] | None = None,
    parallel: int = 3,
):
    """Run evaluation for gaps in parallel, with caching."""
    import random

    gaps = load_gaps(name)
    total_gaps = len(gaps)

    # Sample gaps if requested
    if max_gaps and max_gaps < len(gaps):
        gaps = random.sample(gaps, max_gaps)

    # Print header
    if skill_path:
        print("\nEval Results (with skill)")
        print("=" * 25)
        print(f"Skill: {skill_path}")
    else:
        print("\nEval Results (baseline, no skill)")
        print("=" * 34)
    if max_gaps and max_gaps < total_gaps:
        print(f"Gaps: {len(gaps)} (sampled from {total_gaps})")
    else:
        print(f"Gaps: {len(gaps)}")
    print(f"Samples: {samples} per gap")
    print(f"Parallel: {parallel}")
    print(f"Tools: {', '.join(allowed_tools) if allowed_tools else 'all'}")
    print(f"Total runs: {len(gaps) * samples}")
    print()

    # Build task list
    tasks = []
    for gap_idx, gap in enumerate(gaps):
        for i in range(samples):
            tasks.append(
                {
                    "gap_idx": gap_idx,
                    "gap_source": gap["_source"],
                    "gap_content": gap["_content"],
                    "iteration": i + 1,
                    "total_iterations": samples,
                    "prompt": gap["prompt"],
                    "expected": gap["expected"],
                }
            )

    # Create display
    display = LiveDisplay(tasks)

    # Run with semaphore for parallelism control
    semaphore = asyncio.Semaphore(parallel)

    async def run_with_semaphore(task):
        async with semaphore:
            return await run_single_eval(task, name, skill_path, allowed_tools, display)

    # Start spinner animation
    await display.start()

    # Run all tasks
    results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

    # Stop spinner and finalize display
    await display.stop()
    display.finalize()

    # Count cached vs fresh
    cached_count = sum(1 for r in results if r.get("cached"))
    fresh_count = len(results) - cached_count

    # Calculate stats
    total_pass = sum(1 for r in results if r["pass"])
    total_runs = len(results)
    overall_rate = total_pass / total_runs * 100 if total_runs > 0 else 0

    print()
    if cached_count > 0:
        print(f"Cache: {cached_count} cached, {fresh_count} fresh")
    print(f"Overall pass rate: {overall_rate:.0f}% ({total_pass}/{total_runs})")

    # Generate summary of failures if any
    failures = [r for r in results if not r["pass"]]
    if failures and fresh_count > 0:  # Only summarize if we ran fresh evals
        print()
        print("What Claude did instead:")
        summary = await summarize_responses(failures)
        print(summary)


async def summarize_responses(results: list[dict]) -> str:
    """Summarize what Claude actually did across failed responses."""
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    response_summaries = []
    for result in results:
        response_summaries.append(
            {
                "expected": result.get("expected", ""),
                "response_preview": result["response"][:500] if result.get("response") else "",
                "judgment": result["judgment"]["reasoning"] if result.get("judgment") else "",
            }
        )

    responses_yaml = yaml.dump(response_summaries, default_flow_style=False)
    summary_prompt = f"""Analyze these AI responses that failed to meet expectations.
Summarize the PATTERNS in what the AI did instead.

## Failed Responses

{responses_yaml}

## Your Task

Write 2-4 bullet points summarizing what the AI typically did instead of expected.
Be specific and concise. Format as: - Pattern description (X% of responses)

Focus on the FORMAT or BEHAVIOR patterns, not the content quality.
"""

    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
    )

    result = ""
    async for message in query(prompt=summary_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text

    return result
