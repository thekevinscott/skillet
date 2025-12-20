"""Extract scripts from eval data."""


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
