"""Tests for print_tune_result function."""

from pathlib import Path
from unittest.mock import patch

from skillet.cli.commands.tune.print_result import print_tune_result
from skillet.tune.result import RoundResult, TuneConfig, TuneResult


def _make_tune_result(rounds: list[RoundResult]) -> TuneResult:
    """Create a TuneResult with the given rounds."""
    result = TuneResult.create(
        eval_set="test",
        skill_path=Path("/test/skill.md"),
        original_skill="original",
        config=TuneConfig(
            max_rounds=5,
            target_pass_rate=100.0,
            samples=1,
            parallel=1,
        ),
    )
    for r in rounds:
        result.add_round(r)
    result.finalize(success=len(rounds) > 0 and rounds[-1].pass_rate >= 100)
    return result


def describe_print_tune_result():
    """Tests for print_tune_result function."""

    def it_prints_improvement_message_when_improved():
        """Shows green message when pass rate improved."""
        rounds = [
            RoundResult(round=1, pass_rate=50.0, skill_content="v1", tip_used=None, evals=[]),
            RoundResult(round=2, pass_rate=80.0, skill_content="v2", tip_used="tip", evals=[]),
        ]
        result = _make_tune_result(rounds)

        with patch("skillet.cli.commands.tune.print_result.console") as mock_console:
            print_tune_result(result)

            # Check that improvement message was printed
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Improved" in call for call in calls)
            assert any("50" in call and "80" in call for call in calls)

    def it_prints_no_improvement_when_unchanged():
        """Shows yellow message when no improvement."""
        rounds = [
            RoundResult(round=1, pass_rate=50.0, skill_content="v1", tip_used=None, evals=[]),
            RoundResult(round=2, pass_rate=50.0, skill_content="v2", tip_used="tip", evals=[]),
        ]
        result = _make_tune_result(rounds)

        with patch("skillet.cli.commands.tune.print_result.console") as mock_console:
            print_tune_result(result)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("No improvement" in call for call in calls)

    def it_prints_no_improvement_when_regression():
        """Shows no improvement message even when later rounds are worse.

        Since TuneResult.add_round tracks the best round, a "regression" is really
        just no improvement from baseline (the best remains round 1).
        """
        rounds = [
            RoundResult(round=1, pass_rate=80.0, skill_content="v1", tip_used=None, evals=[]),
            RoundResult(round=2, pass_rate=60.0, skill_content="v2", tip_used="tip", evals=[]),
        ]
        result = _make_tune_result(rounds)

        with patch("skillet.cli.commands.tune.print_result.console") as mock_console:
            print_tune_result(result)

            calls = [str(call) for call in mock_console.print.call_args_list]
            # Best is still 80% from round 1, so no improvement over baseline
            assert any("No improvement" in call for call in calls)
            assert any("80" in call for call in calls)

    def it_prints_rounds_completed():
        """Shows number of rounds completed."""
        rounds = [
            RoundResult(round=1, pass_rate=50.0, skill_content="v1", tip_used=None, evals=[]),
            RoundResult(round=2, pass_rate=60.0, skill_content="v2", tip_used="tip", evals=[]),
            RoundResult(round=3, pass_rate=70.0, skill_content="v3", tip_used="tip", evals=[]),
        ]
        result = _make_tune_result(rounds)

        with patch("skillet.cli.commands.tune.print_result.console") as mock_console:
            print_tune_result(result)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("3 rounds" in call for call in calls)

    def it_handles_empty_rounds():
        """Handles edge case of no rounds with clear message."""
        result = _make_tune_result([])

        with patch("skillet.cli.commands.tune.print_result.console") as mock_console:
            print_tune_result(result)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("No rounds completed" in call for call in calls)
