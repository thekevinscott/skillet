"""Live display for parallel eval runs."""

import asyncio

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .thresholds import get_rate_color

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

    def _build_table(self) -> Table:
        """Build the status table."""
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
