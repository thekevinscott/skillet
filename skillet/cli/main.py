"""skillet CLI - evaluation-driven Claude Code skill development."""
# skillet: allow-multiple-public-callables

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

app = App(
    name="skillet",
    help="Evaluation-driven Claude Code skill development.",
)


@app.command
async def eval(  # noqa: PLR0913
    name: str,
    skill: Annotated[Path | None, Parameter(name="skill")] = None,
    *,
    samples: Annotated[int, Parameter(name=["--samples", "-s"])] = 3,
    max_evals: Annotated[int | None, Parameter(name=["--max-evals", "-m"])] = None,
    tools: Annotated[str | None, Parameter(name=["--tools"])] = None,
    parallel: Annotated[int, Parameter(name=["--parallel", "-p"])] = 3,
    skip_cache: Annotated[bool, Parameter(name=["--skip-cache"])] = False,
    trust: Annotated[bool, Parameter(name=["--trust"])] = False,
    no_summary: Annotated[bool, Parameter(name=["--no-summary"])] = False,
):
    """Evaluate Claude against captured evals.

    NAME can be:
    - A name (looks in ~/.skillet/evals/<name>/)
    - A path to a directory (loads all .yaml files recursively)
    - A path to a single .yaml file

    Results are cached by eval content hash and skill content hash.

    Without SKILL: measures baseline performance (no skill active)
    With SKILL: measures performance with the skill loaded

    SECURITY: Evals may contain setup/teardown scripts that execute shell commands.
    You will be prompted before running evals with scripts. Use --trust to skip
    the prompt (for automation or when you've reviewed the scripts).

    Examples:
        skillet eval browser-fallback                              # baseline
        skillet eval browser-fallback ~/.claude/skills/browser-fallback  # with skill
        skillet eval ./evals/my-skill/001.yaml skill/              # single file
        skillet eval browser-fallback -s 5                         # 5 samples per eval
        skillet eval my-skill -m 5 -s 1                            # 5 random evals, 1 sample each
        skillet eval my-skill -p 5                                 # 5 parallel workers
        skillet eval my-skill --skip-cache                         # ignore cached results
        skillet eval my-skill --trust                              # skip script confirmation
        skillet eval my-skill --no-summary                           # skip failure summary
    """
    from skillet.cli.commands.eval import eval_command

    allowed_tools = [t.strip() for t in tools.split(",")] if tools else None
    await eval_command(
        name,
        skill_path=skill,
        samples=samples,
        max_evals=max_evals,
        allowed_tools=allowed_tools,
        parallel=parallel,
        skip_cache=skip_cache,
        trust=trust,
        no_summary=no_summary,
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
    output: Annotated[Path | None, Parameter(name=["--output", "-o"])] = None,
):
    """Iteratively tune a skill until evals pass.

    Runs evals, analyzes failures, improves the skill, and repeats
    until the target pass rate is reached or max rounds hit.

    The skill file is updated with the best version after tuning completes.
    All iterations are also saved in the output JSON.

    Results are saved to ~/.skillet/tunes/{eval_name}/{timestamp}.json by default.

    Examples:
        skillet tune browser-fallback ~/.claude/skills/browser-fallback
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -t 80
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -r 10
        skillet tune browser-fallback ~/.claude/skills/browser-fallback -s 3
        skillet tune browser-fallback skill/ -o custom_output.json
    """
    from skillet.cli.commands.tune import tune_command

    await tune_command(
        name,
        skill,
        max_rounds=rounds,
        target_pass_rate=target,
        samples=samples,
        parallel=parallel,
        output_path=output,
    )


@app.command
async def create(
    name: str,
    *,
    dir: Annotated[Path | None, Parameter(name=["--dir", "-d"])] = None,
    prompt: Annotated[str | None, Parameter(name=["--prompt"])] = None,
):
    """Create a new skill from captured evals.

    Generates a SKILL.md based on evals in ~/.skillet/evals/<name>/.
    Output is always written to <dir>/.claude/skills/<name>/SKILL.md

    Examples:
        skillet create browser-fallback                  # ~/.claude/skills/browser-fallback/
        skillet create browser-fallback -d .             # ./.claude/skills/browser-fallback/
        skillet create browser-fallback -d /tmp/myproj
        skillet create browser-fallback --prompt "Be concise"
    """
    from skillet.cli.commands.create import create_command

    base = Path.home() if dir is None else dir
    output_dir = base / ".claude" / "skills"
    await create_command(name, output_dir=output_dir, extra_prompt=prompt)


@app.command
async def lint(
    path: Annotated[Path | None, Parameter(name="path")] = None,
    *,
    list_rules: Annotated[bool, Parameter(name=["--list-rules"])] = False,
    no_llm: Annotated[bool, Parameter(name=["--no-llm"])] = False,
):
    """Lint a SKILL.md file for common issues.

    Examples:
        skillet lint path/to/SKILL.md
        skillet lint --no-llm path/to/SKILL.md
        skillet lint --list-rules
    """
    from skillet.cli.commands.lint import lint_command
    from skillet.cli.commands.lint.print_rules import print_rules

    if list_rules:
        print_rules()
        return

    if path is None:
        from skillet.cli import console

        console.print("[red]Error:[/red] path is required unless --list-rules is specified")
        raise SystemExit(2)

    await lint_command(path, include_llm=not no_llm)


@app.command
def show(
    name: str,
    *,
    eval: Annotated[str | None, Parameter(name=["--eval", "-e"])] = None,
    skill: Annotated[Path | None, Parameter(name=["--skill", "-s"])] = None,
):
    """Show cached eval results.

    Displays a summary of cached results for each eval, including
    pass rates and iteration counts. No evals are re-run.

    Use --eval to show detailed iteration results for a specific eval.
    Use --skill to show results with a skill loaded instead of baseline.

    Examples:
        skillet show browser-fallback
        skillet show browser-fallback --eval 001.yaml
        skillet show browser-fallback --skill path/to/skill
        skillet show browser-fallback --skill path/to/skill --eval 001.yaml
    """
    from skillet.cli.commands.show import show_command

    show_command(name, eval_source=eval, skill_path=skill)


@app.command(name="generate-evals")
async def generate_evals_cmd(
    skill: Path,
    *,
    output: Annotated[Path | None, Parameter(name=["--output", "-o"])] = None,
    max_per_category: Annotated[int, Parameter(name=["--max"])] = 5,
    domain: Annotated[list[str] | None, Parameter(name=["--domain", "-d"])] = None,
):
    """Generate candidate evals from a SKILL.md.

    Examples:
        skillet generate-evals path/to/SKILL.md
        skillet generate-evals path/to/SKILL.md --domain triggering
        skillet generate-evals path/to/SKILL.md -d triggering -d functional
    """
    from skillet.cli.commands.generate_evals import generate_evals_command

    await generate_evals_command(
        skill,
        output_dir=output,
        max_per_category=max_per_category,
        domain=domain,
    )


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
