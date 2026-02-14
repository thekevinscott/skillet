"""CLI handler for lint command."""

import sys
from pathlib import Path

from skillet.cli import console
from skillet.errors import LintError
from skillet.lint import lint_skill


async def lint_command(path: Path, *, include_llm: bool = True) -> None:
    """Lint a SKILL.md file and display findings."""
    try:
        result = await lint_skill(path, include_llm=include_llm)
    except LintError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(2)

    if result.findings:
        for finding in result.findings:
            line_info = f":{finding.line}" if finding.line else ""
            console.print(f"{path}{line_info}: [{finding.severity.value}] {finding.message}")
        console.print(f"\n[yellow]{len(result.findings)} finding(s)[/yellow]")
        sys.exit(1)
    else:
        console.print("[green]No issues found[/green]")
