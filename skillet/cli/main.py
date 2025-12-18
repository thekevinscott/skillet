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
    skip_cache: Annotated[bool, Parameter(name=["--skip-cache"])] = False,
):
    """Evaluate Claude against captured gaps.

    NAME can be:
    - A name (looks in ~/.skillet/evals/<name>/)
    - A path to a directory (loads all .yaml files recursively)
    - A path to a single .yaml file

    Results are cached by gap content hash and skill content hash.

    Without SKILL: measures baseline performance (no skill active)
    With SKILL: measures performance with the skill loaded

    Examples:
        skillet eval browser-fallback                              # baseline
        skillet eval browser-fallback ~/.claude/skills/browser-fallback  # with skill
        skillet eval ./evals/my-skill/001.yaml skill/              # single file
        skillet eval browser-fallback -s 5                         # 5 samples per gap
        skillet eval my-skill -g 5 -s 1                            # 5 random gaps, 1 sample each
        skillet eval my-skill -p 5                                 # 5 parallel workers
        skillet eval my-skill --skip-cache                         # ignore cached results
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
        skip_cache=skip_cache,
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
def tune(
    name: str,
    skill: Path,
    *,
    trials: Annotated[int, Parameter(name=["--trials", "-t"])] = 5,
    optimizer: Annotated[str, Parameter(name=["--optimizer", "-O"])] = "bootstrap",
    output: Annotated[Path | None, Parameter(name=["--output", "-o"])] = None,
):
    """Tune a skill using DSPy optimization.

    Uses DSPy's optimization framework to improve skill instructions.
    The original skill file is NOT modified.

    For small datasets (~10 evals), use BootstrapFewShot (default).
    For larger datasets (200+), use MIPROv2.

    Results are saved to ~/.skillet/tunes/{eval_name}/{timestamp}.json by default.

    Examples:
        skillet tune add-command .claude/commands/skillet/add.md
        skillet tune add-command skill/ --optimizer mipro
        skillet tune add-command skill/ -t 10
        skillet tune add-command skill/ -o results.json
    """
    from skillet.cli.commands.tune import tune_command

    tune_command(
        name,
        skill,
        num_trials=trials,
        optimizer=optimizer,
        output_path=output,
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
