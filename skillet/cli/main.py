"""skillet CLI - evaluation-driven Claude Code skill development."""

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

app = App(
    name="skillet",
    help="Evaluation-driven Claude Code skill development.",
)


@app.command
async def eval(
    name: str,
    skill: Annotated[Path | None, Parameter(name="skill")] = None,
    *,
    samples: Annotated[int, Parameter(name=["--samples", "-s"])] = 3,
    gaps: Annotated[int | None, Parameter(name=["--gaps", "-g"])] = None,
    tools: Annotated[str | None, Parameter(name=["--tools", "-t"])] = None,
    parallel: Annotated[int, Parameter(name=["--parallel", "-p"])] = 3,
):
    """Evaluate Claude against captured gaps.

    Reads gap YAML files from ~/.skillet/gaps/<name>/ and runs each prompt
    through Claude, using LLM-as-judge to evaluate against expected behavior.

    Results are cached by gap content hash and skill content hash.

    Without SKILL: measures baseline performance (no skill active)
    With SKILL: measures performance with the skill loaded

    Examples:
        skillet eval browser-fallback                              # baseline
        skillet eval browser-fallback ~/.claude/skills/browser-fallback  # with skill
        skillet eval browser-fallback -s 5                         # 5 samples per gap
        skillet eval my-skill -g 5 -s 1                            # 5 random gaps, 1 sample each
        skillet eval my-skill -p 5                                 # 5 parallel workers
    """
    from skillet.cli.commands.eval import eval_command

    allowed_tools = [t.strip() for t in tools.split(",")] if tools else None
    await eval_command(
        name,
        skill_path=skill,
        samples=samples,
        max_gaps=gaps,
        allowed_tools=allowed_tools,
        parallel=parallel,
    )


@app.command
def compare(
    name: str,
    skill: Path,
):
    """Compare baseline vs skill results from cache.

    Shows a side-by-side comparison of cached baseline and skill results.
    Run `skillet eval <name>` and `skillet eval <name> <skill>` first to populate the cache.

    Examples:
        skillet compare browser-fallback ~/.claude/skills/browser-fallback
    """
    from skillet.cli.commands.compare import compare_command

    compare_command(name, skill)


@app.command
async def tune(
    name: str,
    skill: Path,
    *,
    rounds: Annotated[int, Parameter(name=["--rounds", "-r"])] = 5,
    target: Annotated[float, Parameter(name=["--target", "-t"])] = 100.0,
    samples: Annotated[int, Parameter(name=["--samples", "-s"])] = 1,
    parallel: Annotated[int, Parameter(name=["--parallel", "-p"])] = 3,
):
    """Iteratively tune a skill until evals pass.

    Runs evals, analyzes failures, improves SKILL.md, and repeats
    until the target pass rate is reached or max rounds hit.

    Examples:
        skillet tune browser-fallback ~/.claude/skills/browser-fallback
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -t 80
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -r 10
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -s 3
    """
    from skillet.cli.commands.tune import tune_command

    await tune_command(
        name,
        skill,
        max_rounds=rounds,
        target_pass_rate=target,
        samples=samples,
        parallel=parallel,
    )


@app.command
async def new(
    name: str,
    *,
    dir: Annotated[Path | None, Parameter(name=["--dir", "-d"])] = None,
    prompt: Annotated[str | None, Parameter(name=["--prompt", "-p"])] = None,
):
    """Create a new skill from captured gaps.

    Generates a SKILL.md based on gaps in ~/.skillet/gaps/<name>/.
    Output is always written to <dir>/.claude/skills/<name>/SKILL.md

    Examples:
        skillet new browser-fallback                  # ~/.claude/skills/browser-fallback/
        skillet new browser-fallback -d .             # ./.claude/skills/browser-fallback/
        skillet new browser-fallback -d /tmp/myproj   # /tmp/myproj/.claude/skills/browser-fallback/
        skillet new browser-fallback -p "Be concise"
    """
    from skillet.cli.commands.new import new_command

    base = Path.home() if dir is None else dir
    output_dir = base / ".claude" / "skills"
    await new_command(name, output_dir=output_dir, extra_prompt=prompt)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
