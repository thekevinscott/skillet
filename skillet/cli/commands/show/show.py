"""CLI handler for show command."""

from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from skillet.cli import console
from skillet.cli.display.get_rate_color import get_rate_color
from skillet.show import show
from skillet.show.result import ShowResult

RESPONSE_PREVIEW_LENGTH = 200


def show_command(name: str, eval_source: str | None = None, skill_path: Path | None = None):
    """Display cached eval results."""
    result = show(name, eval_source=eval_source, skill_path=skill_path)

    if eval_source:
        _print_detail(result)
    else:
        _print_summary(result)


def _print_summary(result: ShowResult):
    """Print summary table of all evals."""
    table = Table(title=f"Cached Results: {result.name}")
    table.add_column("Eval", style="cyan")
    table.add_column("Iterations", justify="right")
    table.add_column("Pass Rate", justify="right")

    for eval_data in result.evals:
        count = len(eval_data.iterations)
        if eval_data.pass_rate is not None:
            color = get_rate_color(eval_data.pass_rate)
            rate_str = f"[{color}]{eval_data.pass_rate:.0f}%[/{color}]"
        else:
            rate_str = "[dim]-[/dim]"

        table.add_row(eval_data.source, str(count), rate_str)

    console.print(table)


def _print_detail(result: ShowResult):
    """Print detailed iteration results for filtered evals."""
    for eval_data in result.evals:
        console.print(f"\n[bold cyan]{eval_data.source}[/bold cyan]")

        if not eval_data.iterations:
            console.print("[dim]No cached results[/dim]")
            continue

        for it in eval_data.iterations:
            status = "[green]PASS[/green]" if it.get("pass") else "[red]FAIL[/red]"
            console.print(f"\n  Iteration {it.get('iteration', '?')}  {status}")

            # Tool calls
            tool_calls = it.get("tool_calls", [])
            if tool_calls:
                tools = ", ".join(tc["name"] for tc in tool_calls)
                console.print(f"  Tools: {tools}")

            # Judgment
            judgment = it.get("judgment", {})
            if judgment.get("reasoning"):
                console.print(f"  Judgment: {judgment['reasoning']}")

            # Response (truncated)
            response = it.get("response", "")
            if response:
                preview = (
                    response[:RESPONSE_PREVIEW_LENGTH] + "..."
                    if len(response) > RESPONSE_PREVIEW_LENGTH
                    else response
                )
                console.print(Panel(preview, title="Response", border_style="dim"))
