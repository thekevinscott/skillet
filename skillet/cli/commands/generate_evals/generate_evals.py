"""CLI handler for generate-evals command."""

from pathlib import Path

from skillet.cli import console

from .print_analysis_summary import print_analysis_summary
from .print_candidates_table import print_candidates_table
from .print_dry_run_output import print_dry_run_output
from .print_output_summary import print_output_summary
from .run_generation import run_generation


async def generate_evals_command(
    skill_path: Path,
    *,
    output_dir: Path | None = None,
    use_lint: bool = True,
    max_per_category: int = 5,
    dry_run: bool = False,
) -> None:
    """Run generate-evals command with display."""
    skill_path = Path(skill_path).expanduser().resolve()

    # Determine output directory
    if output_dir is None and not dry_run:
        parent = skill_path.parent if skill_path.is_file() else skill_path
        output_dir = parent / "candidates"

    # Generate candidates with spinner
    result = await run_generation(
        skill_path,
        output_dir=None if dry_run else output_dir,
        use_lint=use_lint,
        max_per_category=max_per_category,
    )

    # Display results
    print_analysis_summary(result.analysis)
    print_candidates_table(result.candidates)

    console.print()
    if dry_run:
        print_dry_run_output(result.candidates)
    elif output_dir:
        print_output_summary(result.candidates, output_dir)
