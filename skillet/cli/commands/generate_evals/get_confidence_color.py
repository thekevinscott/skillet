"""Get color based on confidence level."""

# Thresholds for confidence coloring
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6


def get_confidence_color(confidence: float) -> str:
    """Get color based on confidence level."""
    if confidence >= HIGH_CONFIDENCE:
        return "green"
    if confidence >= MEDIUM_CONFIDENCE:
        return "yellow"
    return "red"
