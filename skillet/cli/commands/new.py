"""CLI handler for new command."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from skillet.cli import console
from skillet.errors import SkillError
from skillet.gaps import load_gaps
from skillet.skill import create_skill


async def new_command(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
):
    """Run new command with display."""
    # Load gaps first to get count
    gaps = load_gaps(name)

    if not gaps:
        raise SkillError(f"No gap files found for '{name}'")

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
            f"Drafting SKILL.md from {len(gaps)} gaps for [cyan]{name}[/cyan]...",
            total=None,
        )
        result = await create_skill(name, output_dir, extra_prompt, overwrite=overwrite)

    # Output summary with tree
    console.print()
    tree = Tree(f"[bold green]Created[/bold green] [cyan]{result['skill_dir']}/[/cyan]")
    tree.add(f"SKILL.md [dim](draft from {result['gap_count']} gaps)[/dim]")
    console.print(tree)

    # Next steps
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{result['skill_dir']}/SKILL.md[/cyan]")
    console.print(f"  2. Run: [bold]skillet eval {name} {result['skill_dir']}[/bold]")
    console.print(f"  3. Compare: [bold]skillet compare {name} {result['skill_dir']}[/bold]")
