"""Compare baseline vs skill eval results from cache."""

from pathlib import Path

# removed click
import yaml

from skillet.cache import (
    CACHE_DIR,
    gap_cache_key,
    get_cached_iterations,
    hash_directory,
)

SKILLET_DIR = Path.home() / ".skillet"


def load_gaps(name: str) -> list[dict]:
    """Load all gap files for a skill from ~/.skillet/gaps/<name>/."""
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise Exception(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        content = gap_file.read_text()
        gap = yaml.safe_load(content)
        gap["_source"] = gap_file.name
        gap["_content"] = content
        gaps.append(gap)

    return gaps


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


def run_compare(name: str, skill_path: Path):
    """Compare baseline vs skill results from cache."""
    gaps = load_gaps(name)

    if not gaps:
        raise Exception(f"No gaps found for '{name}'")

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

    # Check for missing data
    if missing_baseline:
        print(f"Warning: No baseline cache for: {', '.join(missing_baseline)}")
        print(f"Run: skillet eval {name}")
        print()

    if missing_skill:
        print(f"Warning: No skill cache for: {', '.join(missing_skill)}")
        print(f"Run: skillet eval {name} {skill_path}")
        print()

    if missing_baseline and len(missing_baseline) == len(gaps):
        raise Exception("No baseline results cached. Run `skillet eval {name}` first.")

    if missing_skill and len(missing_skill) == len(gaps):
        msg = f"No skill results cached. Run `skillet eval {name} {skill_path}` first."
        raise Exception(msg)

    # Print comparison table
    print(f"Comparison: {name}")
    print("=" * 50)
    print()

    # Header
    print(f"{'Gap':<20} {'Baseline':>10} {'Skill':>10} {'Δ':>10}")
    print("-" * 50)

    # Per-gap results
    for r in results:
        baseline_str = f"{r['baseline']:.0f}%" if r["baseline"] is not None else "-"
        skill_str = f"{r['skill']:.0f}%" if r["skill"] is not None else "-"

        if r["baseline"] is not None and r["skill"] is not None:
            delta = r["skill"] - r["baseline"]
            delta_str = f"{delta:+.0f}%"
        else:
            delta_str = "-"

        print(f"{r['source']:<20} {baseline_str:>10} {skill_str:>10} {delta_str:>10}")

    # Overall
    print("-" * 50)

    overall_baseline = baseline_pass / baseline_total * 100 if baseline_total > 0 else None
    overall_skill = skill_pass / skill_total * 100 if skill_total > 0 else None

    baseline_str = f"{overall_baseline:.0f}%" if overall_baseline is not None else "-"
    skill_str = f"{overall_skill:.0f}%" if overall_skill is not None else "-"

    if overall_baseline is not None and overall_skill is not None:
        delta = overall_skill - overall_baseline
        delta_str = f"{delta:+.0f}%"
    else:
        delta_str = "-"

    print(f"{'Overall':<20} {baseline_str:>10} {skill_str:>10} {delta_str:>10}")
