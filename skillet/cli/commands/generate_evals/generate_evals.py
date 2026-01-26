"""CLI handler for generate-evals command."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from skillet.cli import console
from skillet.generate import generate_evals


async def generate_evals_command(
    skill_path: Path,
    *,
    output_dir: Path | None = None,
    max_per_category: int = 5,
    dry_run: bool = False,
) -> None:
    """Run generate-evals with progress spinner."""
    skill_path = Path(skill_path).expanduser().resolve()
    final_output = None if dry_run else output_dir

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Generating evals from {skill_path.name}...", total=None)
        result = await generate_evals(
            skill_path,
            output_dir=final_output,
            max_per_category=max_per_category,
        )

    console.print(f"Generated {len(result.candidates)} candidates")
