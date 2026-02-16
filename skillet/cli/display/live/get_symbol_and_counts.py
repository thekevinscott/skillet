"""Resolve an iteration's state to a display symbol and pass/done flags."""

from .status_symbols import CACHED, FAIL, PASS, PENDING, RUNNING


def get_symbol_and_counts(it: dict) -> tuple[str, bool, bool]:
    """Get symbol for iteration state, and whether it passed/is done."""
    state = it["state"]
    if state == "pending":
        return PENDING, False, False
    if state == "running":
        return RUNNING, False, False
    # cached or done
    passed = it["result"] and it["result"].get("pass")
    if state == "cached":
        return CACHED, passed, True
    # done
    return PASS if passed else FAIL, passed, True
