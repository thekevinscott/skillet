"""Tests for build_iteration_cache."""

from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from skillet._internal.cache import INFRA_FAILURE_KEY, build_iteration_cache
from skillet._internal.cache.hash_directory import hash_directory
from skillet.agent import Agent


def describe_build_iteration_cache():
    """Tests for the eval iteration cache builder."""

    def _task(iteration=1, eval_source="001.yaml", eval_content="content"):
        return {
            "iteration": iteration,
            "eval_source": eval_source,
            "eval_content": eval_content,
        }

    def it_builds_baseline_path_without_skill():
        cache = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)

        path = cache._get_path(_task(iteration=2))

        # <root>/<name>/<eval-key>/<agent>/baseline/iter-2.cache
        assert path.name == "iter-2.cache"
        assert path.parent.name == "baseline"
        assert path.parent.parent.name == "claude"
        assert path.parent.parent.parent.parent.name == "my-evals"

    def it_builds_skill_path_with_hash(tmp_path: Path):
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("instructions")

        cache = build_iteration_cache(Path("/cache"), "my-evals", skill, Agent.CLAUDE)
        path = cache._get_path(_task())

        # <root>/<name>/<eval-key>/<agent>/skills/<hash>/iter-1.cache
        assert path.parent.name == hash_directory(skill)
        assert path.parent.parent.name == "skills"
        assert path.parent.parent.parent.name == "claude"

    def it_hashes_skill_once_at_build_time(tmp_path: Path):
        skill = tmp_path / "skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("instructions")

        with patch(
            "skillet._internal.cache.build_iteration_cache.hash_directory",
            wraps=hash_directory,
        ) as spy:
            cache = build_iteration_cache(Path("/cache"), "my-evals", skill, Agent.CLAUDE)
            # Resolving paths for several iterations must not re-hash the skill.
            cache._get_path(_task(iteration=1))
            cache._get_path(_task(iteration=2))

        spy.assert_called_once()

    def it_keys_path_by_eval_and_iteration():
        cache = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)

        same = cache._get_path(_task(iteration=1, eval_source="a.yaml"))
        other_iter = cache._get_path(_task(iteration=2, eval_source="a.yaml"))
        other_eval = cache._get_path(_task(iteration=1, eval_source="b.yaml"))

        assert same != other_iter
        assert same != other_eval

    def it_keys_path_by_agent():
        claude = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)
        codex = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CODEX)

        # The agent segments the path so the two agents never collide.
        assert claude._get_path(_task()) != codex._get_path(_task())
        assert claude._get_path(_task()).parent.parent.name == "claude"
        assert codex._get_path(_task()).parent.parent.name == "codex"

    def it_skips_caching_infra_failures():
        cache = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)

        assert cache.condition is not None
        assert cache.condition({"pass": False, INFRA_FAILURE_KEY: True}) is False

    def it_caches_real_eval_outcomes():
        cache = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)

        assert cache.condition is not None
        # Both a genuine pass and a genuine fail are cached.
        assert cache.condition({"pass": True}) is True
        assert cache.condition({"pass": False}) is True

    def it_uses_a_long_duration():
        cache = build_iteration_cache(Path("/cache"), "my-evals", None, Agent.CLAUDE)

        assert cache.duration > timedelta(days=365)
