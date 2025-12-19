"""Calculate pass rate from iteration results."""


def calculate_pass_rate(iterations: list[dict]) -> float | None:
    """Calculate pass rate from iteration results."""
    if not iterations:
        return None
    passes = sum(1 for it in iterations if it.get("pass"))
    return passes / len(iterations) * 100
