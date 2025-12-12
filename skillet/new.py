"""Create a new skill from captured gaps."""

from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

SKILLET_DIR = Path.home() / ".skillet"
console = Console()


class SkillError(Exception):
    """Error during skill creation."""


def load_gaps(name: str) -> list[dict]:
    """Load gaps from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts
    """
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise SkillError(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise SkillError(f"Not a directory: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        with gap_file.open() as f:
            gap = yaml.safe_load(f)
            gaps.append(gap)

    return gaps


async def draft_skill(name: str, gaps: list[dict], extra_prompt: str | None = None) -> str:
    """Use Claude to draft a SKILL.md based on captured gaps."""
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

    gaps_summary = "\n\n".join(
        [
            f"## Gap {i + 1}\nPrompt: {g['prompt']}\nExpected: {g['expected']}"
            for i, g in enumerate(gaps)
        ]
    )

    extra_section = ""
    if extra_prompt:
        extra_section = f"\n# Additional Instructions\n\n{extra_prompt}\n"

    prompt = f"""Draft a minimal SKILL.md to address these gaps.

# Gaps for "{name}"

{gaps_summary}
{extra_section}
# Requirements

- YAML frontmatter with `name` and `description` (description: what + when to trigger)
- Minimal instructions - just enough to pass the expected behavior
- No lengthy explanations or comprehensive documentation
- One or two short examples maximum

Return ONLY the SKILL.md content."""

    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
    )

    result = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text

    result = result.strip()

    # Strip markdown code fences if present
    if result.startswith("```markdown"):
        result = result[len("```markdown") :].strip()
    if result.startswith("```"):
        result = result[3:].strip()
    if result.endswith("```"):
        result = result[:-3].strip()

    return result


async def create_skill(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
):
    """Create a new skill from captured gaps.

    Args:
        name: Skill name (gaps loaded from ~/.skillet/gaps/<name>/)
        output_dir: Where to create the skill (default: ~/.claude/skills)
        extra_prompt: Additional instructions for generating the SKILL.md
    """
    # Load gaps
    gaps = load_gaps(name)

    if not gaps:
        raise SkillError(f"No gap files found for '{name}'")

    skill_dir = output_dir / name

    # Check if already exists
    if skill_dir.exists():
        response = console.input(
            f"[yellow]Skill already exists at {skill_dir}. Overwrite?[/yellow] [y/N] "
        )
        if response.lower() not in ("y", "yes"):
            raise SystemExit(0)
        import shutil

        shutil.rmtree(skill_dir)

    # Generate SKILL.md content with spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(
            f"Drafting SKILL.md from {len(gaps)} gaps for [cyan]{name}[/cyan]...", total=None
        )
        skill_content = await draft_skill(name, gaps, extra_prompt)

    # Create directory and write SKILL.md
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_content + "\n")

    # Output summary with tree
    console.print()
    tree = Tree(f"[bold green]Created[/bold green] [cyan]{skill_dir}/[/cyan]")
    tree.add(f"SKILL.md [dim](draft from {len(gaps)} gaps)[/dim]")
    console.print(tree)

    # Next steps
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{skill_dir}/SKILL.md[/cyan]")
    console.print(f"  2. Run: [bold]skillet eval {name} {skill_dir}[/bold]")
    console.print(f"  3. Compare: [bold]skillet compare {name} {skill_dir}[/bold]")
