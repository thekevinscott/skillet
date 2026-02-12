# /// script
# requires-python = ">=3.12"
# dependencies = ["pyskillet>=0.2.17"]
# ///
"""Evaluate a single skill: generate evals, then run them."""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def log(msg: str) -> None:
    print(msg, flush=True)


async def on_eval_status(task: dict, state: str, result: dict | None) -> None:
    src = task["eval_source"]
    iteration = task["iteration"]
    if state == "cached":
        log(f"  [cached] {src} #{iteration}")
    elif state == "running":
        log(f"  [running] {src} #{iteration} ...")
    elif state == "done" and result:
        verdict = "PASS" if result["pass"] else "FAIL"
        log(f"  [{verdict}] {src} #{iteration}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate evals for a skill and evaluate it.")
    parser.add_argument("skill", type=Path, help="Path to SKILL.md or directory containing it")
    parser.add_argument(
        "--evals-dir",
        type=Path,
        default=Path("./evals"),
        help="Directory for generated eval YAML files (default: ./evals)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("./results"),
        help="Directory for evaluation result JSON (default: ./results)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Iterations per eval (default: 3)",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=5,
        help="Max evals per category for generation (default: 5)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=3,
        help="Parallel eval workers (default: 3)",
    )
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Ignore skillet's internal eval cache",
    )
    args = parser.parse_args()

    skill_path = args.skill.resolve()
    evals_dir = args.evals_dir.resolve()
    results_dir = args.results_dir.resolve()

    from skillet import evaluate, generate_evals

    # Step 1: Generate evals (skip if directory already has YAML files)
    if not any(evals_dir.glob("*.yaml")):
        log(f"Generating evals for {skill_path} (this makes an LLM call, may take ~30s) ...")
        evals_dir.mkdir(parents=True, exist_ok=True)
        result = await generate_evals(
            skill_path, output_dir=evals_dir, max_per_category=args.max_per_category
        )
        log(f"Generated {len(result.candidates)} evals in {evals_dir}")
    else:
        log(f"Evals already exist in {evals_dir}, skipping generation")

    # Step 2: Evaluate (skip if results.json already exists)
    results_file = results_dir / "results.json"
    if not results_file.exists():
        log(f"Evaluating {evals_dir} ...")
        try:
            eval_result = await evaluate(
                name=str(evals_dir),
                skill_path=skill_path,
                samples=args.samples,
                parallel=args.parallel,
                skip_cache=args.skip_cache,
                on_status=on_eval_status,
            )
        except (asyncio.CancelledError, RuntimeError) as e:
            if isinstance(e, RuntimeError) and "cancel scope" not in str(e):
                raise
            # anyio cancel scope cleanup error from claude_agent_sdk.
            # Results are cached individually by skillet — re-run will pick them up.
            log("  (SDK cleanup error — individual results are cached, re-run to collect)")
            return
        results_dir.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(eval_result, indent=2, default=str))
        log(
            f"Pass rate: {eval_result['pass_rate']:.0f}% "
            f"({eval_result['total_pass']}/{eval_result['total_runs']})"
        )
    else:
        log(f"Results already exist at {results_file}, skipping evaluation")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
