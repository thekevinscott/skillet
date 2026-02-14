"""Integration tests for the show API."""

from pathlib import Path

import yaml

from .conftest import create_eval_file


def _populate_cache(
    skillet_dir: Path,
    name: str,
    eval_source: str,
    eval_content: str,
    iterations: list[dict],
    skill_path: Path | None = None,
):
    """Write iteration YAML files into a cache directory."""
    from skillet._internal.cache import eval_cache_key, hash_directory

    eval_key = eval_cache_key(eval_source, eval_content)
    base = skillet_dir / "cache" / name / eval_key

    if skill_path is None:
        cache_dir = base / "baseline"
    else:
        skill_hash = hash_directory(skill_path)
        cache_dir = base / "skills" / skill_hash

    cache_dir.mkdir(parents=True)

    for it in iterations:
        with (cache_dir / f"iter-{it['iteration']}.yaml").open("w") as f:
            yaml.dump(it, f, default_flow_style=False)


def describe_show():
    def it_returns_cached_results_for_an_eval_set(skillet_env: Path):
        from skillet.show import show

        skillet_dir = skillet_env / ".skillet"
        evals_dir = skillet_dir / "evals" / "my-evals"
        evals_dir.mkdir(parents=True)

        eval_file = evals_dir / "001.yaml"
        create_eval_file(eval_file)
        eval_content = eval_file.read_text()

        _populate_cache(
            skillet_dir,
            "my-evals",
            "001.yaml",
            eval_content,
            [
                {
                    "iteration": 1,
                    "response": "I did the thing",
                    "tool_calls": [{"name": "Bash", "input": {"command": "ls"}}],
                    "judgment": {"pass": True, "reasoning": "Correct"},
                    "pass": True,
                },
                {
                    "iteration": 2,
                    "response": "Wrong answer",
                    "tool_calls": [],
                    "judgment": {"pass": False, "reasoning": "Did not match"},
                    "pass": False,
                },
            ],
        )

        result = show("my-evals")

        assert result["name"] == "my-evals"
        assert len(result["evals"]) == 1

        eval_result = result["evals"][0]
        assert eval_result["source"] == "001.yaml"
        assert eval_result["pass_rate"] == 50.0
        assert len(eval_result["iterations"]) == 2
        assert eval_result["iterations"][0]["pass"] is True
        assert eval_result["iterations"][1]["pass"] is False

    def it_filters_to_a_single_eval_with_eval_source(skillet_env: Path):
        from skillet.show import show

        skillet_dir = skillet_env / ".skillet"
        evals_dir = skillet_dir / "evals" / "filter-test"
        evals_dir.mkdir(parents=True)

        eval1 = evals_dir / "001.yaml"
        create_eval_file(eval1)
        eval2 = evals_dir / "002.yaml"
        create_eval_file(eval2, prompt="Different prompt")

        _populate_cache(
            skillet_dir,
            "filter-test",
            "001.yaml",
            eval1.read_text(),
            [
                {
                    "iteration": 1,
                    "response": "Response for eval 001",
                    "tool_calls": [{"name": "Bash", "input": {"command": "ls"}}],
                    "judgment": {"pass": True, "reasoning": "Looks good"},
                    "pass": True,
                },
            ],
        )
        _populate_cache(
            skillet_dir,
            "filter-test",
            "002.yaml",
            eval2.read_text(),
            [
                {
                    "iteration": 1,
                    "response": "Response for eval 002",
                    "tool_calls": [],
                    "judgment": {"pass": False, "reasoning": "Wrong"},
                    "pass": False,
                },
            ],
        )

        result = show("filter-test", eval_source="001.yaml")

        assert len(result["evals"]) == 1
        assert result["evals"][0]["source"] == "001.yaml"
        assert result["evals"][0]["iterations"][0]["response"] == "Response for eval 001"

    def it_returns_skill_results_when_skill_path_is_provided(skillet_env: Path):
        from skillet.show import show

        skillet_dir = skillet_env / ".skillet"
        evals_dir = skillet_dir / "evals" / "skill-test"
        evals_dir.mkdir(parents=True)

        eval_file = evals_dir / "001.yaml"
        create_eval_file(eval_file)
        eval_content = eval_file.read_text()

        # Create a skill file
        skill_dir = skillet_env / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill\nDo the thing.\n")

        # Populate baseline cache
        _populate_cache(
            skillet_dir,
            "skill-test",
            "001.yaml",
            eval_content,
            [
                {
                    "iteration": 1,
                    "response": "baseline response",
                    "tool_calls": [],
                    "judgment": {"pass": False, "reasoning": "No skill"},
                    "pass": False,
                }
            ],
        )
        # Populate skill cache
        _populate_cache(
            skillet_dir,
            "skill-test",
            "001.yaml",
            eval_content,
            [
                {
                    "iteration": 1,
                    "response": "skill response",
                    "tool_calls": [],
                    "judgment": {"pass": True, "reasoning": "Skill helped"},
                    "pass": True,
                }
            ],
            skill_path=skill_dir,
        )

        # Without skill_path -> baseline
        baseline_result = show("skill-test")
        assert baseline_result["evals"][0]["pass_rate"] == 0.0

        # With skill_path -> skill results
        skill_result = show("skill-test", skill_path=skill_dir)
        assert skill_result["evals"][0]["pass_rate"] == 100.0
        assert skill_result["evals"][0]["iterations"][0]["response"] == "skill response"

    def it_returns_empty_iterations_when_no_cache_exists(skillet_env: Path):
        from skillet.show import show

        skillet_dir = skillet_env / ".skillet"
        evals_dir = skillet_dir / "evals" / "no-cache"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        result = show("no-cache")

        assert result["name"] == "no-cache"
        assert len(result["evals"]) == 1
        assert result["evals"][0]["iterations"] == []
        assert result["evals"][0]["pass_rate"] is None
