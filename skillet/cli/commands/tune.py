"""CLI handler for tune command."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from skillet.cli import console
from skillet.gaps import load_gaps
from skillet.tune import TuneResult, tune


def _get_default_output_path(name: str) -> Path:
    """Generate default output path for tune results.

    Returns ~/.skillet/tunes/{eval_name}/{timestamp}.json
    """
    # Extract eval name from path if it's a path
    eval_name = Path(name).name if "/" in name or "\\" in name else name

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    return Path.home() / ".skillet" / "tunes" / eval_name / f"{timestamp}.json"


def tune_command(
    name: str,
    skill_path: Path,
    num_trials: int = 5,
    optimizer: str = "bootstrap",
    output_path: Path | None = None,
) -> TuneResult:
    """Run tune command with display.

    Args:
        name: Name of eval set
        skill_path: Path to skill file
        num_trials: Number of optimization trials
        optimizer: Optimizer type ("bootstrap" or "mipro")
        output_path: Optional path to save results JSON (defaults to ~/.skillet/tunes/)

    Returns:
        TuneResult with optimization results
    """
    gaps = load_gaps(name)

    # Validate optimizer type
    opt: Literal["bootstrap", "mipro"] = "mipro" if optimizer == "mipro" else "bootstrap"

    # Default output path if not provided
    if output_path is None:
        output_path = _get_default_output_path(name)

    # Print header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Tuning:[/bold] {name}\n"
            f"[bold]Skill:[/bold] [cyan]{skill_path}[/cyan]\n"
            f"[bold]Evals:[/bold] {len(gaps)}\n"
            f"[bold]Optimizer:[/bold] {optimizer}\n"
            f"[bold]Trials:[/bold] {num_trials}",
            title="DSPy Skill Tuner",
        )
    )
    console.print()

    # Run optimization with progress spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Optimizing skill with DSPy...", total=None)
        result = tune(
            name,
            skill_path,
            num_trials=num_trials,
            optimizer=opt,
        )

    # Display results
    console.print()
    original = result.result.original_score
    optimized = result.result.optimized_score
    delta = result.result.delta

    if delta > 0:
        console.print(
            f"[bold green]✓ Improved: "
            f"{original:.0%} → {optimized:.0%} (+{delta:.0%})[/bold green]"
        )
    elif delta == 0:
        console.print(f"[bold yellow]→ No improvement: {original:.0%}[/bold yellow]")
    else:
        console.print(
            f"[bold red]✗ Regression: "
            f"{original:.0%} → {optimized:.0%} ({delta:.0%})[/bold red]"
        )

    # Show optimized skill preview
    console.print()
    console.print("[dim]Optimized skill preview:[/dim]")
    preview = result.optimized_skill[:500]
    if len(result.optimized_skill) > 500:
        preview += "..."
    console.print(f"[dim]{preview}[/dim]")

    # Save results
    result.save(output_path)
    console.print(f"\n[dim]Results saved to:[/dim] {output_path}")

    return result
