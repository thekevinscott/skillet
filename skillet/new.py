"""Create a new skill from captured gaps."""

import asyncio
import json
from pathlib import Path

import click
import yaml


SKILLET_DIR = Path.home() / ".skillet"


def load_gaps(name: str) -> list[dict]:
    """Load gaps from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts
    """
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise click.ClickException(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise click.ClickException(f"Not a directory: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        with open(gap_file) as f:
            gap = yaml.safe_load(f)
            gaps.append(gap)

    return gaps


async def draft_skill_async(name: str, gaps: list[dict]) -> str:
    """Use Claude to draft a SKILL.md based on captured gaps."""
    from claude_agent_sdk import query, AssistantMessage, TextBlock, ClaudeAgentOptions

    gaps_summary = "\n\n".join([
        f"## Gap {i+1}\nPrompt: {g['prompt']}\nExpected: {g['expected']}"
        for i, g in enumerate(gaps)
    ])

    prompt = f"""Draft a minimal SKILL.md to address these gaps.

# Gaps for "{name}"

{gaps_summary}

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

    return result.strip()


def draft_skill(name: str, gaps: list[dict]) -> str:
    """Sync wrapper for draft_skill_async."""
    return asyncio.run(draft_skill_async(name, gaps))


def minimal_template(name: str) -> str:
    """Return a minimal SKILL.md template when no gaps exist."""
    return f"""---
name: {name}
description: TODO - describe what this skill does and when to use it
---

# {name.replace('-', ' ').title()}

TODO: Add instructions for Claude here.

## Examples

TODO: Add examples of expected behavior.
"""


def create_skill(
    name: str,
    output_dir: str = "plugins",
    version: str = "0.1.0",
    description: str | None = None,
):
    """Create a new skill plugin structure.

    Args:
        name: Skill name (gaps loaded from ~/.skillet/gaps/<name>/)
        output_dir: Where to create the plugin (default: plugins/)
        version: Plugin version (default: 0.1.0)
        description: Plugin description (default: auto-generated)
    """
    # Load gaps
    gaps = load_gaps(name)

    output_path = Path(output_dir)
    plugin_dir = output_path / name
    plugin_json_dir = plugin_dir / ".claude-plugin"
    skills_dir = plugin_dir / "skills" / name

    # Check if already exists
    if plugin_dir.exists():
        if not click.confirm(f"Plugin already exists at {plugin_dir}. Overwrite?"):
            raise SystemExit(0)
        import shutil
        shutil.rmtree(plugin_dir)

    # Generate SKILL.md content
    if gaps:
        click.echo(f"Found {len(gaps)} gaps for '{name}', drafting SKILL.md...")
        skill_content = draft_skill(name, gaps)
    else:
        raise click.ClickException(f"No gap files found in {gaps_path}")

    # Create directory structure
    plugin_json_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Write plugin.json
    plugin_json = {
        "name": name,
        "version": version,
        "description": description or f"Claude Code skill: {name}",
    }
    (plugin_json_dir / "plugin.json").write_text(json.dumps(plugin_json, indent=2) + "\n")

    # Write SKILL.md
    (skills_dir / "SKILL.md").write_text(skill_content + "\n")

    # Output summary
    click.echo()
    click.echo(f"Created {plugin_dir}/")
    click.echo(f"├── .claude-plugin/")
    click.echo(f"│   └── plugin.json")
    click.echo(f"└── skills/{name}/")
    if gaps:
        click.echo(f"    └── SKILL.md (draft from {len(gaps)} gaps)")
    else:
        click.echo(f"    └── SKILL.md (minimal template)")
    click.echo()
    click.echo(f"Next: edit SKILL.md, then run:")
    click.echo(f"  skillet eval {name}")
