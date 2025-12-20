"""Script detection and confirmation for eval command."""

from skillet.cli import console


def get_scripts_from_evals(evals: list[dict]) -> list[tuple[str, str, str]]:
    """Extract all scripts from evals.

    Returns list of (source, script_type, script_content) tuples.
    """
    scripts = []
    for eval_data in evals:
        source = eval_data.get("_source", "unknown")
        if eval_data.get("setup"):
            scripts.append((source, "setup", eval_data["setup"]))
        if eval_data.get("teardown"):
            scripts.append((source, "teardown", eval_data["teardown"]))
    return scripts


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
        if len(first_line) > 60:
            first_line = first_line[:57] + "..."
        console.print(f"    [cyan]{first_line}[/cyan]")

    console.print()
    console.print("[dim]Use --trust to skip this prompt in the future.[/dim]")
    console.print()

    try:
        response = console.input("[bold]Run these scripts? [y/N][/bold] ")
        return response.lower() in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False
