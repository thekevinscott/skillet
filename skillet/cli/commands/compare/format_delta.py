"""Format delta values with color."""


def format_delta(baseline: float | None, skill: float | None) -> str:
    """Format delta with color."""
    if baseline is None or skill is None:
        return "-"
    delta = skill - baseline
    if delta > 0:
        return f"[green]+{delta:.0f}%[/green]"
    elif delta < 0:
        return f"[red]{delta:.0f}%[/red]"
    else:
        return "0%"
