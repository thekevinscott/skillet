"""Display thresholds for pass rate coloring."""

# Pass rate thresholds for color coding
PASS_RATE_GREEN = 80  # >= 80% shows green
PASS_RATE_YELLOW = 50  # >= 50% shows yellow, below shows red


def get_rate_color(pass_rate: float) -> str:
    """Get color for pass rate display."""
    if pass_rate >= PASS_RATE_GREEN:
        return "green"
    if pass_rate >= PASS_RATE_YELLOW:
        return "yellow"
    return "red"
