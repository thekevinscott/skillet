"""skillet CLI - evaluation-driven Claude Code skill development."""

from pathlib import Path

import click


@click.group()
@click.version_option()
def main():
    """skillet: Evaluation-driven Claude Code skill development."""
    pass


@main.command()
@click.argument("name")
@click.argument("skill", default=None, required=False, type=click.Path(exists=True))
@click.option("--samples", "-s", default=3, help="Number of samples per gap (default: 3)")
@click.option("--gaps", "-g", default=None, type=int, help="Number of gaps to sample (random)")
@click.option("--tools", "-t", default=None, help="Comma-separated list of allowed tools (default: all)")
@click.option("--parallel", "-p", default=3, help="Number of parallel workers (default: 3)")
def eval(name: str, skill: str | None, samples: int, gaps: int | None, tools: str | None, parallel: int):
    """Evaluate Claude against captured gaps.

    Reads gap YAML files from ~/.skillet/gaps/<name>/ and runs each prompt
    through Claude, using LLM-as-judge to evaluate against expected behavior.

    Results are cached by gap content hash and skill content hash.

    \b
    Without SKILL: measures baseline performance (no skill active)
    With SKILL: measures performance with the skill loaded

    Example:
        skillet eval browser-fallback                              # baseline
        skillet eval browser-fallback ~/.claude/skills/browser-fallback  # with skill
        skillet eval browser-fallback -s 5                         # 5 samples per gap
        skillet eval my-skill -g 5 -s 1                            # 5 random gaps, 1 sample each
        skillet eval my-skill -p 5                                 # 5 parallel workers
    """
    from skillet.eval import run_eval

    # Parse tools list
    allowed_tools = None  # None means all tools
    if tools:
        allowed_tools = [t.strip() for t in tools.split(",")]

    skill_path = Path(skill) if skill else None
    run_eval(name, skill_path=skill_path, samples=samples, max_gaps=gaps, allowed_tools=allowed_tools, parallel=parallel)


@main.command()
@click.argument("name")
@click.argument("skill", type=click.Path(exists=True))
def compare(name: str, skill: str):
    """Compare baseline vs skill results from cache.

    Shows a side-by-side comparison of cached baseline and skill results.
    Run `skillet eval <name>` and `skillet eval <name> <skill>` first to populate the cache.

    Example:
        skillet compare browser-fallback ~/.claude/skills/browser-fallback
    """
    from skillet.compare import run_compare

    run_compare(name, Path(skill))


@main.command()
@click.argument("name")
@click.argument("skill", type=click.Path(exists=True), required=True)
@click.option("--rounds", "-r", default=5, help="Maximum tuning rounds (default: 5)")
@click.option("--target", "-t", default=100.0, help="Target pass rate percentage (default: 100)")
@click.option("--samples", "-s", default=1, help="Samples per gap during eval (default: 1)")
@click.option("--parallel", "-p", default=3, help="Number of parallel workers (default: 3)")
def tune(name: str, skill: str, rounds: int, target: float, samples: int, parallel: int):
    """Iteratively tune a skill until evals pass.

    Runs evals, analyzes failures, improves SKILL.md, and repeats
    until the target pass rate is reached or max rounds hit.

    Example:
        skillet tune browser-fallback ~/.claude/skills/browser-fallback
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -t 80
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -r 10
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -s 3
    """
    from skillet.tune import run_tune

    run_tune(
        name,
        Path(skill),
        max_rounds=rounds,
        target_pass_rate=target,
        samples=samples,
        parallel=parallel,
    )


@main.command()
@click.argument("name")
@click.option("--dir", "-d", default=None, type=click.Path(), help="Project root directory (default: ~, outputs to <dir>/.claude/skills/)")
@click.option("--prompt", "-p", default=None, help="Additional instructions for generating the SKILL.md")
def new(name: str, dir: str | None, prompt: str | None):
    """Create a new skill from captured gaps.

    Generates a SKILL.md based on gaps in ~/.skillet/gaps/<name>/.
    Output is always written to <dir>/.claude/skills/<name>/SKILL.md

    Example:
        skillet new browser-fallback                  # ~/.claude/skills/browser-fallback/
        skillet new browser-fallback -d .             # ./.claude/skills/browser-fallback/
        skillet new browser-fallback -d /tmp/myproj   # /tmp/myproj/.claude/skills/browser-fallback/
        skillet new browser-fallback -p "Be concise"
    """
    from skillet.new import create_skill

    # Default to home directory
    if dir is None:
        base = Path.home()
    else:
        base = Path(dir)

    output_dir = base / ".claude" / "skills"
    create_skill(name, output_dir=str(output_dir), extra_prompt=prompt)


if __name__ == "__main__":
    main()
