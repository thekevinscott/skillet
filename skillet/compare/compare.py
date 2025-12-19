"""Compare baseline vs skill eval results from cache."""

from pathlib import Path

from skillet.errors import EmptyFolderError
from skillet.evals import load_evals

from .calculate_pass_rate import calculate_pass_rate
from .get_cached_results_for_eval import get_cached_results_for_eval


def compare(name: str, skill_path: Path) -> dict:
    """Compare baseline vs skill results from cache.

    Returns:
        dict with per-eval results, overall stats, and warnings
    """
    evals = load_evals(name)

    if not evals:
        raise EmptyFolderError(f"No evals found for '{name}'")

    # Collect results for each eval
    results = []
    baseline_total = 0
    baseline_pass = 0
    skill_total = 0
    skill_pass = 0
    missing_baseline = []
    missing_skill = []

    for eval_item in evals:
        baseline_iters = get_cached_results_for_eval(name, eval_item, None)
        skill_iters = get_cached_results_for_eval(name, eval_item, skill_path)

        baseline_rate = calculate_pass_rate(baseline_iters)
        skill_rate = calculate_pass_rate(skill_iters)

        if baseline_rate is None:
            missing_baseline.append(eval_item["_source"])
        else:
            baseline_total += len(baseline_iters)
            baseline_pass += sum(1 for it in baseline_iters if it.get("pass"))

        if skill_rate is None:
            missing_skill.append(eval_item["_source"])
        else:
            skill_total += len(skill_iters)
            skill_pass += sum(1 for it in skill_iters if it.get("pass"))

        results.append(
            {
                "source": eval_item["_source"],
                "baseline": baseline_rate,
                "skill": skill_rate,
            }
        )

    # Calculate overall rates
    overall_baseline = baseline_pass / baseline_total * 100 if baseline_total > 0 else None
    overall_skill = skill_pass / skill_total * 100 if skill_total > 0 else None

    return {
        "name": name,
        "skill_path": skill_path,
        "results": results,
        "overall_baseline": overall_baseline,
        "overall_skill": overall_skill,
        "baseline_total": baseline_total,
        "baseline_pass": baseline_pass,
        "skill_total": skill_total,
        "skill_pass": skill_pass,
        "missing_baseline": missing_baseline,
        "missing_skill": missing_skill,
    }
