"""Live display for parallel eval runs."""

import asyncio

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .get_rate_color import get_rate_color

console = Console()

# Status symbols with colors
PENDING = "[dim]○[/dim]"
CACHED = "[blue]●[/blue]"
RUNNING = "[yellow]◐[/yellow]"
PASS = "[green]✓[/green]"
FAIL = "[red]✗[/red]"

# Rows reserved for content above/below the live table (headers, stats, etc.)
DISPLAY_OVERHEAD = 5


class LiveDisplay:
    """Live updating display for parallel eval runs using rich."""

    def __init__(self, tasks: list[dict]):
        """Initialize with list of tasks."""
        self.tasks = tasks
        self.status = {self._key(t): {"state": "pending", "result": None} for t in tasks}
        self.lock = asyncio.Lock()
        self.live: Live | None = None
        self._eval_count = len({t["eval_idx"] for t in tasks})

    def _key(self, task: dict) -> str:
        return f"{task['eval_idx']}:{task['iteration']}"

    def _get_symbol_and_counts(self, it: dict) -> tuple[str, bool, bool]:
        """Get symbol for iteration state, and whether it passed/is done."""
        state = it["state"]
        if state == "pending":
            return PENDING, False, False
        if state == "running":
            return RUNNING, False, False
        # cached or done
        passed = it["result"] and it["result"].get("pass")
        if state == "cached":
            return CACHED, passed, True
        # done
        return PASS if passed else FAIL, passed, True

    def _should_compact(self) -> bool:
        """Use compact mode when evals exceed available terminal rows."""
        available = console.size.height - DISPLAY_OVERHEAD
        return self._eval_count > available

    def _count_by_status(self) -> dict[str, int]:
        """Count samples by status category."""
        counts = {"pass": 0, "fail": 0, "running": 0, "cached": 0, "pending": 0}
        for s in self.status.values():
            state = s["state"]
            if state == "pending":
                counts["pending"] += 1
            elif state == "running":
                counts["running"] += 1
            elif state == "cached":
                counts["cached"] += 1
            else:
                result = s["result"]
                if isinstance(result, dict) and result.get("pass"):
                    counts["pass"] += 1
                else:
                    counts["fail"] += 1
        return counts

    def _format_compact_parts(self, counts: dict[str, int]) -> str:
        """Format compact summary from status counts."""
        parts = [f"[bold]{self._eval_count} evals[/bold]"]
        if counts["pass"]:
            parts.append(f"[green]✓ {counts['pass']}[/green]")
        if counts["fail"]:
            parts.append(f"[red]✗ {counts['fail']}[/red]")
        if counts["cached"]:
            parts.append(f"[blue]● {counts['cached']}[/blue]")
        if counts["running"]:
            parts.append(f"[yellow]◐ {counts['running']}[/yellow]")
        if counts["pending"]:
            parts.append(f"[dim]○ {counts['pending']}[/dim]")
        return "  ".join(parts)

    def _build_compact_table(self) -> Table:
        """Build a single-line summary when there are too many evals."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Summary")
        table.add_row(self._format_compact_parts(self._count_by_status()))
        return table

    def _build_table(self) -> Table:
        """Build the status table."""
        if self._should_compact():
            return self._build_compact_table()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Eval", style="cyan")
        table.add_column("Status")

        # Group by eval
        evals = {}
        for task in self.tasks:
            eval_idx = task["eval_idx"]
            if eval_idx not in evals:
                evals[eval_idx] = {"source": task["eval_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            evals[eval_idx]["iterations"].append(status)

        # Build rows
        for eval_idx in sorted(evals.keys()):
            eval_item = evals[eval_idx]
            iterations = eval_item["iterations"]

            symbols = []
            pass_count = 0
            done_count = 0
            for it in iterations:
                symbol, passed, done = self._get_symbol_and_counts(it)
                symbols.append(symbol)
                if passed:
                    pass_count += 1
                if done:
                    done_count += 1

            row_content = " ".join(symbols)
            # Show percentage as soon as all samples for this eval are done
            if done_count == len(iterations) and done_count > 0:
                pct = pass_count / len(iterations) * 100
                pct_color = get_rate_color(pct)
                row_content += f" [{pct_color}]({pct:.0f}%)[/{pct_color}]"

            table.add_row(eval_item["source"], row_content)

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
        if self._should_compact():
            return self._finalize_compact()

        # Group by eval
        evals = {}
        for task in self.tasks:
            eval_idx = task["eval_idx"]
            if eval_idx not in evals:
                evals[eval_idx] = {"source": task["eval_source"], "iterations": []}

            key = self._key(task)
            status = self.status[key]
            evals[eval_idx]["iterations"].append(status)

        # Print final results
        for eval_idx in sorted(evals.keys()):
            eval_item = evals[eval_idx]
            iterations = eval_item["iterations"]

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
            pct_color = get_rate_color(pct)
            console.print(
                f"  [cyan]{eval_item['source']}[/cyan]: {' '.join(symbols)} "
                f"[{pct_color}]({pct:.0f}%)[/{pct_color}]"
            )

    def _finalize_compact(self):
        """Print compact final summary."""
        counts = self._count_by_status()
        pass_count = counts["pass"]
        total = pass_count + counts["fail"]
        pct = pass_count / total * 100 if total else 0
        pct_color = get_rate_color(pct)
        console.print(
            f"  [bold]{self._eval_count} evals[/bold]: "
            f"[green]✓ {pass_count}[/green]  [red]✗ {counts['fail']}[/red]  "
            f"[{pct_color}]({pct:.0f}%)[/{pct_color}]"
        )
