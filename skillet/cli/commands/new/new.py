"""CLI handler for new command."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from skillet.cli import console
from skillet.errors import SkillError
from skillet.evals import load_evals
from skillet.skill import create_skill


async def new_command(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
):
    """Run new command with display."""
    # Load evals first to get count
    evals = load_evals(name)

    if not evals:
        raise SkillError(f"No eval files found for '{name}'")

    skill_dir = output_dir / name

    # Check if already exists
    overwrite = False
    if skill_dir.exists():
        response = console.input(
            f"[yellow]Skill already exists at {skill_dir}. Overwrite?[/yellow] [y/N] "
        )
        if response.lower() not in ("y", "yes"):
            raise SystemExit(0)
        overwrite = True

    # Generate SKILL.md content with spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(
            f"Drafting SKILL.md from {len(evals)} evals for [cyan]{name}[/cyan]...",
            total=None,
        )
        result = await create_skill(name, output_dir, extra_prompt, overwrite=overwrite)

    # Output summary with tree
    console.print()
    tree = Tree(f"[bold green]Created[/bold green] [cyan]{result['skill_dir']}/[/cyan]")
    tree.add(f"SKILL.md [dim](draft from {result['eval_count']} evals)[/dim]")
    console.print(tree)

    # Next steps
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{result['skill_dir']}/SKILL.md[/cyan]")
    console.print(f"  2. Run: [bold]skillet eval {name} {result['skill_dir']}[/bold]")
    console.print(f"  3. Compare: [bold]skillet compare {name} {result['skill_dir']}[/bold]")
