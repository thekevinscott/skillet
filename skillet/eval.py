"""Evaluate Claude against captured gaps, with or without a skill."""

import asyncio
import sys
import threading
import time
from pathlib import Path

import click
import yaml

from skillet.judge import judge_response


class Spinner:
    """A simple spinner for showing progress."""

    def __init__(self, message: str = ""):
        self.message = message
        self.spinning = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0

    def _spin(self):
        while self.spinning:
            frame = self.frames[self.current % len(self.frames)]
            sys.stderr.write(f"\r  {frame} {self.message}")
            sys.stderr.flush()
            self.current += 1
            time.sleep(0.08)

    def start(self, message: str = None):
        if message:
            self.message = message
        self.spinning = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def update(self, message: str):
        self.message = message

    def stop(self, final_message: str = None):
        self.spinning = False
        if self.thread:
            self.thread.join()
        if final_message:
            sys.stderr.write(f"\r  ✓ {final_message}\n")
        else:
            sys.stderr.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stderr.flush()


SKILLET_DIR = Path.home() / ".skillet"


def load_gaps(name: str) -> list[dict]:
    """Load all gap files for a skill from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts
    """
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise click.ClickException(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise click.ClickException(f"Not a directory: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        with open(gap_file) as f:
            gap = yaml.safe_load(f)
            gap["_source"] = gap_file.name
            gaps.append(gap)

    if not gaps:
        raise click.ClickException(f"No gap files found in {gaps_dir}")

    return gaps


async def run_prompt_async(
    prompt: str,
    skill: str | None = None,
    allowed_tools: list[str] | None = None,
) -> str:
    """Run a prompt through Claude and return the response."""
    from claude_agent_sdk import query, AssistantMessage, TextBlock, ClaudeAgentOptions

    # TODO: Load skill into Claude agent when skill path is provided
    # For now, skills need to be loaded via CLI --plugin flag or installed globally
    if skill:
        click.echo(f"  (Note: skill loading via SDK not yet implemented, using installed plugins)")

    options = ClaudeAgentOptions(
        max_turns=3,
        allowed_tools=allowed_tools,  # None means all tools
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


def run_prompt(prompt: str, skill: str | None = None, allowed_tools: list[str] | None = None) -> str:
    """Sync wrapper for run_prompt_async."""
    return asyncio.run(run_prompt_async(prompt, skill, allowed_tools))


async def summarize_responses_async(results: list[dict]) -> str:
    """Summarize what Claude actually did across all responses."""
    from claude_agent_sdk import query, AssistantMessage, TextBlock, ClaudeAgentOptions

    # Collect all responses and their judgments
    response_summaries = []
    for result in results:
        for iteration in result["iterations"]:
            response_summaries.append({
                "expected": result["expected"],
                "response_preview": iteration["response"][:500],
                "judgment": iteration["judgment"]["reasoning"],
            })

    summary_prompt = f"""Analyze these AI responses that failed to meet expectations. Summarize the PATTERNS in what the AI did instead.

## Failed Responses

{yaml.dump(response_summaries, default_flow_style=False)}

## Your Task

Write 2-4 bullet points summarizing what the AI typically did instead of the expected behavior. Be specific and concise. Format as:
  - Pattern description (X% of responses)

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


def summarize_responses(results: list[dict]) -> str:
    """Sync wrapper for summarize_responses_async."""
    return asyncio.run(summarize_responses_async(results))


def run_eval(
    name: str,
    skill: str | None = None,
    iterations: int = 3,
    max_gaps: int | None = None,
    allowed_tools: list[str] | None = None,
):
    """Run evaluation for gaps, optionally with a skill.

    Args:
        name: Skill name (gaps loaded from ~/.skillet/gaps/<name>/)
        skill: Path to skill plugin directory, or None for baseline
        iterations: Number of times to run each gap
        max_gaps: If set, randomly sample this many gaps
        allowed_tools: List of allowed tools, or None for all tools
    """
    import random

    gaps = load_gaps(name)
    total_gaps = len(gaps)

    # Sample gaps if requested
    if max_gaps and max_gaps < len(gaps):
        gaps = random.sample(gaps, max_gaps)

    if skill:
        click.echo(f"\nEval Results (with skill)")
        click.echo("=" * 25)
        click.echo(f"Skill: {skill}")
    else:
        click.echo(f"\nEval Results (baseline, no skill)")
        click.echo("=" * 34)
    if max_gaps and max_gaps < total_gaps:
        click.echo(f"Gaps: {len(gaps)} (sampled from {total_gaps})")
    else:
        click.echo(f"Gaps: {len(gaps)}")
    click.echo(f"Iterations: {iterations} per gap")
    click.echo(f"Tools: {', '.join(allowed_tools) if allowed_tools else 'all'}")
    click.echo(f"Total runs: {len(gaps) * iterations}")
    click.echo()

    results = []
    total_pass = 0
    total_runs = 0

    for gap in gaps:
        gap_results = []
        gap_pass = 0

        click.echo(f"Gap: {gap['_source']}")
        click.echo(f"  Prompt: {gap['prompt'][:50]}...")
        click.echo(f"  Expected: {gap['expected'][:50]}...")

        for i in range(iterations):
            click.echo(f"  [{i + 1}/{iterations}] generating response...")
            response = run_prompt(gap["prompt"], skill, allowed_tools)
            click.echo(f"  Response ({len(response)} chars): {response[:200]}...")
            click.echo()
            click.echo(f"  [{i + 1}/{iterations}] judging response...")
            judgment = judge_response(
                prompt=gap["prompt"],
                response=response,
                expected=gap["expected"],
            )
            click.echo(f"  Judgment: {'PASS' if judgment['pass'] else 'FAIL'} - {judgment['reasoning']}")
            click.echo()

            gap_results.append({
                "iteration": i + 1,
                "response": response,
                "judgment": judgment,
            })

            if judgment["pass"]:
                gap_pass += 1
                total_pass += 1
            total_runs += 1

        pass_rate = gap_pass / iterations * 100
        click.echo(f"  Result: {pass_rate:.0f}% ({gap_pass}/{iterations})")
        click.echo()

        results.append({
            "source": gap["_source"],
            "prompt": gap["prompt"],
            "expected": gap["expected"],
            "pass_rate": pass_rate,
            "iterations": gap_results,
        })

    overall_rate = total_pass / total_runs * 100 if total_runs > 0 else 0
    click.echo(f"Overall pass rate: {overall_rate:.0f}% ({total_pass}/{total_runs})")

    # Generate summary of what Claude actually did
    click.echo()
    click.echo("What Claude did instead:")
    summary = summarize_responses(results)
    click.echo(summary)
