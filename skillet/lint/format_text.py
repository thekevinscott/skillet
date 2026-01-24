"""Text formatter for lint results."""

from .types import LintResult, LintSeverity


def format_text(result: LintResult, *, use_color: bool = True) -> str:
    """Format lint results as human-readable text.

    Args:
        result: The lint result to format
        use_color: Whether to use ANSI color codes

    Returns:
        Formatted text output
    """
    lines = []

    if use_color:
        colors = {
            LintSeverity.ERROR: "\033[31m",  # Red
            LintSeverity.WARNING: "\033[33m",  # Yellow
            LintSeverity.SUGGESTION: "\033[36m",  # Cyan
        }
        reset = "\033[0m"
    else:
        colors = dict.fromkeys(LintSeverity, "")
        reset = ""

    for finding in result.findings:
        color = colors[finding.severity]
        line_part = f":{finding.line}" if finding.line else ""
        col_part = ":1" if finding.line else ""

        line = (
            f"{result.path}{line_part}{col_part}: "
            f"{color}{finding.severity.value}[{finding.rule_id}]{reset}: "
            f"{finding.message}"
        )
        lines.append(line)

    # Summary line
    if result.findings:
        lines.append("")
        parts = []
        if result.error_count:
            s = "s" if result.error_count != 1 else ""
            parts.append(f"{result.error_count} error{s}")
        if result.warning_count:
            s = "s" if result.warning_count != 1 else ""
            parts.append(f"{result.warning_count} warning{s}")
        if result.suggestion_count:
            s = "s" if result.suggestion_count != 1 else ""
            parts.append(f"{result.suggestion_count} suggestion{s}")
        lines.append(", ".join(parts))
    else:
        lines.append("No issues found.")

    return "\n".join(lines)
