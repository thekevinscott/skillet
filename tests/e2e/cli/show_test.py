"""End-to-end tests for the `skillet show` command using curtaincall."""

import hashlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

from curtaincall import Terminal, expect

from skillet._internal.cache import save_iteration

SKILLET = f"{sys.executable} -m skillet.cli.main"


def _populate_cache(
    cache_base: Path,
    eval_key: str,
    iterations: list[dict],
    skill_hash: str | None = None,
):
    """Write iteration files into a cache directory."""
    if skill_hash:
        cache_dir = cache_base / eval_key / "skills" / skill_hash
    else:
        cache_dir = cache_base / eval_key / "baseline"
    for it in iterations:
        save_iteration(cache_dir, it["iteration"], it)


def _make_env(skillet_dir: str) -> dict[str, str]:
    """Build env with SKILLET_DIR pointing to a temp directory."""
    return {**os.environ, "SKILLET_DIR": skillet_dir}


def describe_skillet_show():
    def it_displays_cached_results(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Shows cached eval results via the CLI."""
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        eval_file = evals_dir / "001.yaml"
        eval_file.write_text(
            "timestamp: 2025-01-01T00:00:00Z\n"
            "prompt: 'Summarize this page'\n"
            "expected: 'Uses WebFetch'\n"
            "name: test-show\n"
        )
        eval_content = eval_file.read_text()
        content_hash = hashlib.md5(eval_content.encode()).hexdigest()[:12]
        eval_key = f"001-{content_hash}"

        cache_base = tmp_path / "cache" / evals_dir.resolve().name
        _populate_cache(
            cache_base,
            eval_key,
            [
                {
                    "iteration": 1,
                    "response": "I fetched the page",
                    "tool_calls": [{"name": "WebFetch", "input": {"url": "https://example.com"}}],
                    "judgment": {"pass": True, "reasoning": "Correct"},
                    "pass": True,
                },
            ],
        )

        term = terminal(
            f"{SKILLET} show {evals_dir}",
            env=_make_env(str(tmp_path)),
        )
        expect(term.get_by_text("001.yaml")).to_be_visible()

    def it_displays_detail_view_with_eval_flag(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Shows iteration details when --eval is specified."""
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        eval_file = evals_dir / "001.yaml"
        eval_file.write_text(
            "timestamp: 2025-01-01T00:00:00Z\n"
            "prompt: 'Summarize this page'\n"
            "expected: 'Uses WebFetch'\n"
            "name: test-show\n"
        )
        eval_content = eval_file.read_text()
        content_hash = hashlib.md5(eval_content.encode()).hexdigest()[:12]
        eval_key = f"001-{content_hash}"

        cache_base = tmp_path / "cache" / evals_dir.resolve().name
        _populate_cache(
            cache_base,
            eval_key,
            [
                {
                    "iteration": 1,
                    "response": "I fetched the page",
                    "tool_calls": [{"name": "WebFetch", "input": {"url": "https://example.com"}}],
                    "judgment": {"pass": True, "reasoning": "Correct"},
                    "pass": True,
                },
            ],
        )

        term = terminal(
            f"{SKILLET} show {evals_dir} --eval 001.yaml",
            env=_make_env(str(tmp_path)),
        )
        expect(term.get_by_text("I fetched the page")).to_be_visible()
        expect(term.get_by_text("WebFetch")).to_be_visible()

    def it_displays_skill_results_with_skill_flag(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Shows skill cache results when --skill is specified."""
        from skillet._internal.cache import hash_directory

        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        eval_file = evals_dir / "001.yaml"
        eval_file.write_text(
            "timestamp: 2025-01-01T00:00:00Z\n"
            "prompt: 'Test prompt'\n"
            "expected: 'Expected behavior'\n"
            "name: test-skill-show\n"
        )
        eval_content = eval_file.read_text()
        content_hash = hashlib.md5(eval_content.encode()).hexdigest()[:12]
        eval_key = f"001-{content_hash}"

        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test Skill\n")
        skill_hash = hash_directory(skill_dir)

        cache_base = tmp_path / "cache" / evals_dir.resolve().name
        _populate_cache(
            cache_base,
            eval_key,
            [
                {
                    "iteration": 1,
                    "response": "skill-enhanced response",
                    "tool_calls": [],
                    "judgment": {"pass": True, "reasoning": "Good"},
                    "pass": True,
                }
            ],
            skill_hash=skill_hash,
        )

        term = terminal(
            f"{SKILLET} show {evals_dir} --skill {skill_dir} --eval 001.yaml",
            env=_make_env(str(tmp_path)),
        )
        expect(term.get_by_text("skill-enhanced response")).to_be_visible()
