"""End-to-end tests for the `skillet show` command."""

import hashlib
import shutil
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

from skillet._internal.cache import CACHE_DIR


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
    cache_dir.mkdir(parents=True)
    for it in iterations:
        with (cache_dir / f"iter-{it['iteration']}.yaml").open("w") as f:
            yaml.dump(it, f, default_flow_style=False)


@pytest.fixture
def cache_dir(tmp_path: Path) -> Generator[tuple[Path, Path], None, None]:
    """Create eval files and populate cache, cleaning up after the test."""
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

    cache_base = CACHE_DIR / evals_dir.resolve().name
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

    yield evals_dir, cache_base

    if cache_base.exists():
        shutil.rmtree(cache_base)


def describe_skillet_show():
    def it_displays_cached_results(cache_dir: tuple[Path, Path]):
        """Shows cached eval results via the CLI."""
        evals_dir, _cache_base = cache_dir

        result = subprocess.run(
            [sys.executable, "-m", "skillet.cli.main", "show", str(evals_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"show failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "001.yaml" in result.stdout

    def it_displays_detail_view_with_eval_flag(cache_dir: tuple[Path, Path]):
        """Shows iteration details when --eval is specified."""
        evals_dir, _cache_base = cache_dir

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "show",
                str(evals_dir),
                "--eval",
                "001.yaml",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"show --eval failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "I fetched the page" in result.stdout
        assert "WebFetch" in result.stdout

    def it_displays_skill_results_with_skill_flag(tmp_path: Path):
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

        # Create skill
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test Skill\n")
        skill_hash = hash_directory(skill_dir)

        cache_base = CACHE_DIR / evals_dir.resolve().name
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

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillet.cli.main",
                    "show",
                    str(evals_dir),
                    "--skill",
                    str(skill_dir),
                    "--eval",
                    "001.yaml",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, (
                f"show --skill failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
            assert "skill-enhanced response" in result.stdout
        finally:
            if cache_base.exists():
                shutil.rmtree(cache_base)
