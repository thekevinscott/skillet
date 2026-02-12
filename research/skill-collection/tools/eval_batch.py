# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Batch-evaluate skills from a JSON manifest of paths."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def slug_for_path(path: str) -> str:
    """Deterministic short slug from a skill path."""
    return hashlib.sha256(path.encode()).hexdigest()[:12]


def log(msg: str) -> None:
    print(msg, flush=True)


def run_skill(
    skill_path: str,
    eval_script: Path,
    output_dir: Path,
    args: argparse.Namespace,
) -> dict:
    """Evaluate a single skill. Returns a summary dict."""
    slug = slug_for_path(skill_path)
    skill_dir = output_dir / slug
    evals_dir = skill_dir / "evals"
    results_dir = skill_dir / "results"
    results_file = results_dir / "results.json"

    if results_file.exists():
        result_data = json.loads(results_file.read_text())
        return {
            "path": skill_path,
            "slug": slug,
            "status": "cached",
            "pass_rate": result_data.get("pass_rate"),
        }

    cmd = [
        "uv",
        "run",
        "--no-project",
        str(eval_script),
        skill_path,
        "--evals-dir",
        str(evals_dir),
        "--results-dir",
        str(results_dir),
        "--samples",
        str(args.samples),
        "--max-per-category",
        str(args.max_per_category),
        "--parallel",
        str(args.parallel),
    ]
    if args.skip_cache:
        cmd.append("--skip-cache")
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])

    t0 = time.monotonic()
    for attempt in range(1, 3):
        proc = subprocess.run(cmd, capture_output=False)
        if results_file.exists():
            break
        if proc.returncode != 0:
            break
        # exit 0 but no results = SDK cleanup error, retry to collect from cache
        log(f"  [{skill_path}] retrying ({attempt}/2) ...")
    elapsed = time.monotonic() - t0

    if results_file.exists():
        result_data = json.loads(results_file.read_text())
        pass_rate = result_data.get("pass_rate")
        return {
            "path": skill_path,
            "slug": slug,
            "status": "ok",
            "pass_rate": pass_rate,
            "elapsed": round(elapsed, 1),
        }
    return {
        "path": skill_path,
        "slug": slug,
        "status": "error",
        "exit_code": proc.returncode,
        "elapsed": round(elapsed, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-evaluate skills listed in a JSON file.")
    parser.add_argument(
        "skills_json", type=Path, help="JSON file containing an array of skill paths"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./batch-results"),
        help="Base output directory (default: ./batch-results)",
    )
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--max-per-category", type=int, default=5)
    parser.add_argument("--parallel", type=int, default=1, help="Parallel eval workers per skill")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of skills to evaluate concurrently (default: 1)",
    )
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Timeout in seconds per eval_skill step (0 = no timeout)",
    )
    args = parser.parse_args()

    skills = json.loads(args.skills_json.read_text())
    if not isinstance(skills, list):
        print("Error: JSON file must contain an array of paths", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve eval_skill.py relative to this script
    eval_script = Path(__file__).resolve().parent / "eval_skill.py"
    if not eval_script.exists():
        print(f"Error: {eval_script} not found", file=sys.stderr)
        sys.exit(1)

    # Build manifest mapping slug -> path
    manifest_file = output_dir / "manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
    for skill_path in skills:
        manifest[slug_for_path(skill_path)] = skill_path
    manifest_file.write_text(json.dumps(manifest, indent=2))

    total = len(skills)
    results_summary = []

    if args.concurrency <= 1:
        for i, skill_path in enumerate(skills, 1):
            log(f"[{i}/{total}] {skill_path}")
            result = run_skill(skill_path, eval_script, output_dir, args)
            _log_result(result)
            results_summary.append(result)
    else:
        log(f"Running {total} skills with concurrency={args.concurrency}")
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {
                pool.submit(run_skill, sp, eval_script, output_dir, args): sp for sp in skills
            }
            for future in as_completed(futures):
                result = future.result()
                _log_result(result)
                results_summary.append(result)

    # Write summary
    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(results_summary, indent=2))

    # Print summary
    ok = sum(1 for r in results_summary if r["status"] in ("ok", "cached"))
    failed = sum(1 for r in results_summary if r["status"] == "error")
    log(f"\nDone: {ok} succeeded, {failed} failed out of {total}")
    log(f"Summary: {summary_file}")


def _log_result(result: dict) -> None:
    path = result["path"]
    status = result["status"]
    if status == "cached":
        log(f"  [{path}] skipped (cached) — pass rate: {result.get('pass_rate')}")
    elif status == "ok":
        log(f"  [{path}] done in {result['elapsed']:.0f}s — pass rate: {result['pass_rate']:.0f}%")
    else:
        log(
            f"  [{path}] FAILED (exit {result.get('exit_code')}) after {result.get('elapsed', 0):.0f}s"
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
