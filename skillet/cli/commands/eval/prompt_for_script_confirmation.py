"""Prompt user to confirm script execution."""

from skillet.cli import console

# Maximum lines to display before showing a "... and N more lines" indicator
MAX_DISPLAY_LINES = 10


def prompt_for_script_confirmation(scripts: list[tuple[str, str, str]]) -> bool:
    """Show scripts and prompt user for confirmation.

    Returns True if user confirms, False otherwise.
    """
    console.print()
    console.print("[yellow bold]⚠ Security Warning[/yellow bold]")
    console.print(
        f"These evals contain [bold]{len(scripts)}[/bold] setup/teardown scripts "
        "that will execute shell commands:"
    )
    console.print()

    for source, script_type, script in scripts:
        console.print(f"  [dim]{source}[/dim] ({script_type}):")
        lines = script.split("\n")
        visible = lines[:MAX_DISPLAY_LINES]
        for line in visible:
            console.print(f"    [cyan]{line}[/cyan]")
        remaining = len(lines) - MAX_DISPLAY_LINES
        if remaining > 0:
            console.print(f"    [dim]... and {remaining} more lines[/dim]")

    console.print()
    console.print("[dim]Use --trust to skip this prompt in the future.[/dim]")
    console.print()

    try:
        response = console.input("[bold]Run these scripts? [y/N][/bold] ")
        return response.lower() in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False
