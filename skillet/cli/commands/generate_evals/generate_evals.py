"""CLI handler for generate-evals command."""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from skillet.cli import console
from skillet.generate import generate_evals
from skillet.generate.types import EvalDomain


def _parse_domains(raw: list[str] | None) -> list[EvalDomain] | None:
    """Parse CLI domain strings into EvalDomain enums."""
    if raw is None:
        return None
    valid = {d.value for d in EvalDomain}
    domains = []
    for value in raw:
        lower = value.lower().strip()
        if lower not in valid:
            options = ", ".join(sorted(valid))
            console.print(f"[red]Error:[/red] unknown domain '{value}'. Must be one of: {options}")
            raise SystemExit(2)
        domains.append(EvalDomain(lower))
    return domains


async def generate_evals_command(
    skill_path: Path,
    *,
    output_dir: Path | None = None,
    max_per_category: int = 5,
    domain: list[str] | None = None,
) -> None:
    """Run generate-evals with progress spinner."""
    skill_path = Path(skill_path).expanduser().resolve()
    domains = _parse_domains(domain)

    # Default output alongside the skill
    if output_dir is None:
        parent = skill_path.parent if skill_path.is_file() else skill_path
        output_dir = parent / "candidates"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Generating evals from {skill_path.name}...", total=None)
        result = await generate_evals(
            skill_path,
            output_dir=output_dir,
            max_per_category=max_per_category,
            domains=domains,
        )

    # Display analysis summary
    analysis = result.analysis
    console.print()
    console.print("[bold]Skill Analysis:[/bold]")
    console.print(f"  Name: [cyan]{analysis.get('name', 'unnamed')}[/cyan]")
    console.print(f"  Goals: {len(analysis.get('goals', []))}")
    console.print(f"  Prohibitions: {len(analysis.get('prohibitions', []))}")
    console.print(f"  Examples: {analysis.get('example_count', 0)}")
    # Display candidates table
    console.print()
    table = Table(title=f"Generated {len(result.candidates)} Candidates")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Domain", style="magenta")
    table.add_column("Source")
    for c in result.candidates:
        domain_str = c.domain.value if c.domain else "-"
        table.add_row(c.name, c.category, domain_str, c.source)
    console.print(table)

    # Show output location
    if output_dir:
        console.print()
        console.print(f"Written to [cyan]{output_dir}/[/cyan]")
