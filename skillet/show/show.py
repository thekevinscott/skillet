"""Read cached eval results for display."""

from pathlib import Path

from skillet._internal.cache import get_all_cached_results
from skillet.evals import load_evals

from .result import ShowEvalResult, ShowResult


def show(name: str, eval_source: str | None = None, skill_path: Path | None = None) -> ShowResult:
    """Return cached results for an eval set, grouped by eval source."""
    evals = load_evals(name)
    cached = get_all_cached_results(name, skill_path=skill_path)

    eval_results = []
    for eval_item in evals:
        source = eval_item["_source"]
        if eval_source and source != eval_source:
            continue
        iterations = cached.get(source, [])
        pass_count = sum(1 for it in iterations if it.get("pass"))
        total = len(iterations)
        pass_rate = pass_count / total * 100 if total > 0 else None

        eval_results.append(
            ShowEvalResult(
                source=source,
                iterations=iterations,
                pass_rate=pass_rate,
            )
        )

    return ShowResult(name=name, evals=eval_results)
