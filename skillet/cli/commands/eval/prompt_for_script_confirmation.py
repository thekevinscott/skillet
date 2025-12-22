"""Prompt user to confirm script execution."""

from skillet.cli import console

# Maximum line length for script preview before truncation
MAX_SCRIPT_LINE_LENGTH = 60


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
        # Show first line or truncated script
        first_line = script.split("\n")[0]
        if len(first_line) > MAX_SCRIPT_LINE_LENGTH:
            first_line = first_line[: MAX_SCRIPT_LINE_LENGTH - 3] + "..."
        console.print(f"    [cyan]{first_line}[/cyan]")

    console.print()
    console.print("[dim]Use --trust to skip this prompt in the future.[/dim]")
    console.print()

    try:
        response = console.input("[bold]Run these scripts? [y/N][/bold] ")
        return response.lower() in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False
