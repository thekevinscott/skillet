"""Live display for parallel eval runs."""

import asyncio

from rich.console import Console
from rich.live import Live
from rich.table import Table

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
