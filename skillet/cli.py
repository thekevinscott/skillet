"""skillet CLI - evaluation-driven Claude Code skill development."""

import click


@click.group()
@click.version_option()
def main():
    """skillet: Evaluation-driven Claude Code skill development."""
    pass


@main.command()
@click.argument("name")
@click.option("--skill", "-s", default=None, type=click.Path(exists=True), help="Path to skill plugin directory")
@click.option("--iterations", "-i", default=3, help="Number of iterations per gap")
@click.option("--gaps", "-g", default=None, type=int, help="Number of gaps to sample (random)")
@click.option("--tools", "-t", default=None, help="Comma-separated list of allowed tools (default: all)")
def eval(name: str, skill: str | None, iterations: int, gaps: int | None, tools: str | None):
    """Evaluate Claude against captured gaps.

    Reads gap YAML files from ~/.skillet/gaps/<name>/ and runs each prompt
    through Claude, using LLM-as-judge to evaluate against expected behavior.

    Without --skill: measures baseline performance (no skill active)
    With --skill: measures performance with the skill loaded

    Example:
        skillet eval conventional-comments                     # baseline
        skillet eval conventional-comments -s plugins/conventional-comments  # with skill
        skillet eval browser-fallback -i 5
        skillet eval my-skill -g 5 -i 1  # 5 random gaps, 1 iteration each
    """
    from skillet.eval import run_eval

    # Parse tools list
    allowed_tools = None  # None means all tools
    if tools:
        allowed_tools = [t.strip() for t in tools.split(",")]

    run_eval(name, skill=skill, iterations=iterations, max_gaps=gaps, allowed_tools=allowed_tools)


@main.command()
@click.argument("name")
@click.option("--output", "-o", default="plugins", help="Output directory (default: plugins)")
@click.option("--version", "-v", default="0.1.0", help="Plugin version (default: 0.1.0)")
@click.option("--description", "-d", default=None, help="Plugin description")
def new(name: str, output: str, version: str, description: str | None):
    """Create a new skill from captured gaps.

    Generates plugin structure with a draft SKILL.md based on gaps
    in ~/.skillet/gaps/<name>/.

    Example:
        skillet new conventional-comments
        skillet new browser-fallback -o ./my-plugins
        skillet new my-skill --version 1.0.0
    """
    from skillet.new import create_skill

    create_skill(name, output_dir=output, version=version, description=description)


if __name__ == "__main__":
    main()
