"""Compare baseline vs skill eval results from cache."""

from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from skillet.cache import (
    CACHE_DIR,
    gap_cache_key,
    get_cached_iterations,
    hash_directory,
)

SKILLET_DIR = Path.home() / ".skillet"
console = Console()


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
        console.print(
            f"[yellow]Warning:[/yellow] No baseline cache for: {', '.join(missing_baseline)}"
        )
        console.print(f"Run: [bold]skillet eval {name}[/bold]")
        console.print()

    if missing_skill:
        console.print(f"[yellow]Warning:[/yellow] No skill cache for: {', '.join(missing_skill)}")
        console.print(f"Run: [bold]skillet eval {name} {skill_path}[/bold]")
        console.print()

    if missing_baseline and len(missing_baseline) == len(gaps):
        raise Exception("No baseline results cached. Run `skillet eval {name}` first.")

    if missing_skill and len(missing_skill) == len(gaps):
        msg = f"No skill results cached. Run `skillet eval {name} {skill_path}` first."
        raise Exception(msg)

    # Build comparison table
    table = Table(title=f"Comparison: {name}")
    table.add_column("Gap", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("Skill", justify="right")
    table.add_column("Δ", justify="right")

    # Per-gap results
    for r in results:
        baseline_str = f"{r['baseline']:.0f}%" if r["baseline"] is not None else "-"
        skill_str = f"{r['skill']:.0f}%" if r["skill"] is not None else "-"
        delta_str = format_delta(r["baseline"], r["skill"])

        table.add_row(r["source"], baseline_str, skill_str, delta_str)

    # Overall row
    overall_baseline = baseline_pass / baseline_total * 100 if baseline_total > 0 else None
    overall_skill = skill_pass / skill_total * 100 if skill_total > 0 else None

    baseline_str = f"{overall_baseline:.0f}%" if overall_baseline is not None else "-"
    skill_str = f"{overall_skill:.0f}%" if overall_skill is not None else "-"
    delta_str = format_delta(overall_baseline, overall_skill)

    table.add_section()
    table.add_row("[bold]Overall[/bold]", baseline_str, skill_str, delta_str)

    console.print(table)
