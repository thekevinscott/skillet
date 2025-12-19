"""Tests for tune result data structures."""

import tempfile
from pathlib import Path

from skillet.tune.result import (
    EvalResult,
    RoundResult,
    TuneConfig,
    TuneResult,
)


def describe_TuneResult():
    """Tests for TuneResult class."""

    def it_creates_with_factory():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test-evals",
            skill_path=Path("/path/to/skill"),
            original_skill="# Original skill",
            config=config,
        )

        assert result.metadata.eval_set == "test-evals"
        assert result.metadata.original_skill_path == "/path/to/skill"
        assert result.original_skill == "# Original skill"
        assert result.best_skill == "# Original skill"
        assert result.result.success is False
        assert result.result.final_pass_rate == 0.0

    def it_adds_round_and_tracks_best():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test",
            skill_path=Path("/skill"),
            original_skill="original",
            config=config,
        )

        round1 = RoundResult(
            round=1, pass_rate=0.5, skill_content="skill v1", tip_used=None, evals=[]
        )
        result.add_round(round1)

        assert result.result.rounds_completed == 1
        assert result.result.final_pass_rate == 0.5
        assert result.result.best_round == 1
        assert result.best_skill == "skill v1"

    def it_updates_best_on_higher_pass_rate():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test",
            skill_path=Path("/skill"),
            original_skill="original",
            config=config,
        )

        result.add_round(
            RoundResult(round=1, pass_rate=0.5, skill_content="v1", tip_used=None, evals=[])
        )
        result.add_round(
            RoundResult(round=2, pass_rate=0.8, skill_content="v2", tip_used=None, evals=[])
        )

        assert result.result.best_round == 2
        assert result.best_skill == "v2"

    def it_keeps_best_when_rate_drops():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test",
            skill_path=Path("/skill"),
            original_skill="original",
            config=config,
        )

        result.add_round(
            RoundResult(round=1, pass_rate=0.8, skill_content="v1", tip_used=None, evals=[])
        )
        result.add_round(
            RoundResult(round=2, pass_rate=0.5, skill_content="v2", tip_used=None, evals=[])
        )

        assert result.result.best_round == 1
        assert result.best_skill == "v1"

    def it_finalizes_with_success():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test",
            skill_path=Path("/skill"),
            original_skill="original",
            config=config,
        )
        result.finalize(success=True)

        assert result.result.success is True
        assert result.metadata.completed_at != ""

    def it_converts_to_dict():
        config = TuneConfig(max_rounds=5, target_pass_rate=0.9, samples=10, parallel=2)
        result = TuneResult.create(
            eval_set="test",
            skill_path=Path("/skill"),
            original_skill="original",
            config=config,
        )
        d = result.to_dict()

        assert d["metadata"]["eval_set"] == "test"
        assert d["config"]["max_rounds"] == 5
        assert d["original_skill"] == "original"

    def it_saves_and_loads():
        config = TuneConfig(max_rounds=3, target_pass_rate=0.8, samples=5, parallel=1)
        result = TuneResult.create(
            eval_set="roundtrip-test",
            skill_path=Path("/skill"),
            original_skill="original content",
            config=config,
        )
        result.add_round(
            RoundResult(
                round=1,
                pass_rate=0.6,
                skill_content="improved",
                tip_used="be concise",
                evals=[
                    EvalResult(source="eval1.yaml", passed=True, reasoning="good", response="ok")
                ],
            )
        )
        result.finalize(success=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.json"
            result.save(path)

            loaded = TuneResult.load(path)

            assert loaded.metadata.eval_set == "roundtrip-test"
            assert loaded.config.max_rounds == 3
            assert loaded.original_skill == "original content"
            assert loaded.best_skill == "improved"
            assert len(loaded.rounds) == 1
            assert loaded.rounds[0].pass_rate == 0.6
            assert loaded.rounds[0].evals[0].source == "eval1.yaml"
