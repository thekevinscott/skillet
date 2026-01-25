"""Run generation with progress spinner."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from skillet.cli import console
from skillet.generate import generate_evals
from skillet.generate.types import GenerateResult


async def run_generation(skill_path: Path, **kwargs) -> GenerateResult:
    """Run generation with progress spinner."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(
            f"Analyzing [cyan]{skill_path.name}[/cyan] and generating eval candidates...",
            total=None,
        )
        return await generate_evals(skill_path, **kwargs)
