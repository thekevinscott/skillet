"""Compare baseline vs skill eval results from cache."""

from pathlib import Path

from skillet._internal.cache import (
    CACHE_DIR,
    gap_cache_key,
    get_cached_iterations,
    hash_directory,
)
from skillet.errors import GapError
from skillet.gaps import load_gaps


def get_cached_results_for_gap(name: str, gap: dict, skill_path: Path | None) -> list[dict]:
    """Get cached iteration results for a specific gap."""
    gap_key = gap_cache_key(gap["_source"], gap["_content"])
    cache_base = CACHE_DIR / name / gap_key

    if skill_path is None:
        cache_dir = cache_base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        cache_dir = cache_base / "skills" / skill_hash

    return get_cached_iterations(cache_dir)


def calculate_pass_rate(iterations: list[dict]) -> float | None:
    """Calculate pass rate from iteration results."""
    if not iterations:
        return None
    passes = sum(1 for it in iterations if it.get("pass"))
    return passes / len(iterations) * 100


def compare(name: str, skill_path: Path) -> dict:
    """Compare baseline vs skill results from cache.

    Returns:
        dict with per-gap results, overall stats, and warnings
    """
    gaps = load_gaps(name)

    if not gaps:
        raise GapError(f"No gaps found for '{name}'")

    # Collect results for each gap
    results = []
    baseline_total = 0
    baseline_pass = 0
    skill_total = 0
    skill_pass = 0
    missing_baseline = []
    missing_skill = []

    for gap in gaps:
        baseline_iters = get_cached_results_for_gap(name, gap, None)
        skill_iters = get_cached_results_for_gap(name, gap, skill_path)

        baseline_rate = calculate_pass_rate(baseline_iters)
        skill_rate = calculate_pass_rate(skill_iters)

        if baseline_rate is None:
            missing_baseline.append(gap["_source"])
        else:
            baseline_total += len(baseline_iters)
            baseline_pass += sum(1 for it in baseline_iters if it.get("pass"))

        if skill_rate is None:
            missing_skill.append(gap["_source"])
        else:
            skill_total += len(skill_iters)
            skill_pass += sum(1 for it in skill_iters if it.get("pass"))

        results.append(
            {
                "source": gap["_source"],
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
