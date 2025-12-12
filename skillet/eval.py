"""Evaluate Claude against captured gaps, with or without a skill."""

import asyncio
from pathlib import Path

import yaml
from rich.console import Console
from rich.live import Live
from rich.table import Table

from skillet.cache import (
    gap_cache_key,
    get_cache_dir,
    get_cached_iterations,
    save_iteration,
)
from skillet.judge import judge_response

SKILLET_DIR = Path.home() / ".skillet"
console = Console()

# Status symbols with colors
PENDING = "[dim]○[/dim]"
CACHED = "[blue]●[/blue]"
RUNNING = "[yellow]◐[/yellow]"
PASS = "[green]✓[/green]"
FAIL = "[red]✗[/red]"


class LiveDisplay:
    """Live updating display for parallel eval runs using rich."""

    def __init__(self, tasks: list[dict]):
        """Initialize with list of tasks."""
        self.tasks = tasks
        self.status = {self._key(t): {"state": "pending", "result": None} for t in tasks}
        self.lock = asyncio.Lock()
        self.live: Live | None = None

    def _key(self, task: dict) -> str:
        return f"{task['gap_idx']}:{task['iteration']}"

    def _build_table(self) -> Table:
        """Build the status table."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Gap", style="cyan")
        table.add_column("Status")

        # Group by gap
        gaps = {}
        for task in self.tasks:
            gap_idx = task["gap_idx"]
            if gap_idx not in gaps:
                gaps[gap_idx] = {"source": task["gap_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            gaps[gap_idx]["iterations"].append(status)

        # Build rows
        for gap_idx in sorted(gaps.keys()):
            gap = gaps[gap_idx]
            iterations = gap["iterations"]

            symbols = []
            for it in iterations:
                if it["state"] == "pending":
                    symbols.append(PENDING)
                elif it["state"] == "cached":
                    symbols.append(CACHED)
                elif it["state"] == "running":
                    symbols.append(RUNNING)
                elif it["state"] == "done":
                    if it["result"] and it["result"].get("pass"):
                        symbols.append(PASS)
                    else:
                        symbols.append(FAIL)

            table.add_row(gap["source"], " ".join(symbols))

        return table

    async def start(self):
        """Start the live display."""
        self.live = Live(self._build_table(), console=console, refresh_per_second=4)
        self.live.start()

    async def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()

    async def update(self, task: dict, state: str, result: dict | None = None):
        """Update task status and refresh display."""
        async with self.lock:
            key = self._key(task)
            self.status[key] = {"state": state, "result": result}
            if self.live:
                self.live.update(self._build_table())

    def finalize(self):
        """Print final state with pass rates."""
        # Group by gap
        gaps = {}
        for task in self.tasks:
            gap_idx = task["gap_idx"]
            if gap_idx not in gaps:
                gaps[gap_idx] = {"source": task["gap_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            gaps[gap_idx]["iterations"].append(status)

        # Print final results
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
            pct_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
            console.print(
                f"  [cyan]{gap['source']}[/cyan]: {' '.join(symbols)} "
                f"[{pct_color}]({pct:.0f}%)[/{pct_color}]"
            )


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
    console.print()
    if skill_path:
        console.print("[bold]Eval Results (with skill)[/bold]")
        console.print(f"Skill: [cyan]{skill_path}[/cyan]")
    else:
        console.print("[bold]Eval Results (baseline, no skill)[/bold]")

    if max_gaps and max_gaps < total_gaps:
        console.print(f"Gaps: {len(gaps)} [dim](sampled from {total_gaps})[/dim]")
    else:
        console.print(f"Gaps: {len(gaps)}")
    console.print(f"Samples: {samples} per gap")
    console.print(f"Parallel: {parallel}")
    console.print(f"Tools: {', '.join(allowed_tools) if allowed_tools else 'all'}")
    console.print(f"Total runs: {len(gaps) * samples}")
    console.print()

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

    # Start live display
    await display.start()

    # Run all tasks
    results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

    # Stop live display and show final results
    await display.stop()
    display.finalize()

    # Count cached vs fresh
    cached_count = sum(1 for r in results if r.get("cached"))
    fresh_count = len(results) - cached_count

    # Calculate stats
    total_pass = sum(1 for r in results if r["pass"])
    total_runs = len(results)
    overall_rate = total_pass / total_runs * 100 if total_runs > 0 else 0

    console.print()
    if cached_count > 0:
        console.print(f"Cache: [blue]{cached_count} cached[/blue], {fresh_count} fresh")

    rate_color = "green" if overall_rate >= 80 else "yellow" if overall_rate >= 50 else "red"
    console.print(
        f"Overall pass rate: [{rate_color}]{overall_rate:.0f}%[/{rate_color}] "
        f"({total_pass}/{total_runs})"
    )

    # Generate summary of failures if any
    failures = [r for r in results if not r["pass"]]
    if failures and fresh_count > 0:  # Only summarize if we ran fresh evals
        console.print()
        console.print("[bold]What Claude did instead:[/bold]")
        summary = await summarize_responses(failures)
        console.print(summary)


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
