"""CLI handler for lint command."""

from pathlib import Path

from skillet.cli import console
from skillet.lint import (
    LintSeverity,
    format_json,
    format_text,
    lint,
)

from .print_rules import print_rules
from .severity import severity_meets_threshold


def lint_command(
    path: Path | None,
    *,
    format: str = "text",
    fail_on: str = "error",
    disable: list[str] | None = None,
    list_rules: bool = False,
) -> int:
    """Run lint command with display.

    Args:
        path: Path to skill directory or SKILL.md file (required unless list_rules=True)
        format: Output format ("text" or "json")
        fail_on: Minimum severity to cause non-zero exit ("error", "warning", "suggestion")
        disable: List of rule IDs to disable
        list_rules: If True, list available rules and exit

    Returns:
        Exit code (0 = pass, 1 = findings above threshold, 2 = error)
    """
    if list_rules:
        print_rules()
        return 0

    if path is None:
        console.print("[red]Error:[/red] PATH is required")
        return 2

    try:
        result = lint(path, disabled_rules=disable)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 2

    # Output results
    use_color = format == "text" and console.is_terminal
    if format == "json":
        console.print(format_json(result))
    else:
        console.print(format_text(result, use_color=use_color))

    # Determine exit code based on fail_on threshold
    severity_levels = {
        "error": LintSeverity.ERROR,
        "warning": LintSeverity.WARNING,
        "suggestion": LintSeverity.SUGGESTION,
    }
    threshold = severity_levels.get(fail_on, LintSeverity.ERROR)

    # Check if any findings meet or exceed threshold
    for finding in result.findings:
        if severity_meets_threshold(finding.severity, threshold):
            return 1

    return 0
