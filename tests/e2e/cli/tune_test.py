"""End-to-end tests for the `skillet tune` command."""

import json
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from curtaincall import Terminal, expect

PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"
SKILLET = f"{sys.executable} -m skillet.cli.main"


def describe_skillet_tune():
    """Tests for the `skillet tune` command."""

    @pytest.mark.asyncio
    async def it_tunes_skill_to_target_pass_rate(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        """Test that skillet tune improves a skill to reach target pass rate."""
        evals_dir = tmp_path / "evals" / "pirate"
        evals_dir.mkdir(parents=True)

        command_dir = tmp_path / ".claude" / "commands"
        command_dir.mkdir(parents=True)

        pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
        for eval_file in pirate_evals.glob("*.yaml"):
            (evals_dir / eval_file.name).write_text(eval_file.read_text())

        pirate_command = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_path = command_dir / "pirate.md"
        skill_path.write_text(pirate_command.read_text())

        output_path = tmp_path / "tune_result.json"

        term = terminal(
            f"{SKILLET} tune {evals_dir} {skill_path}"
            f" --target 100 --rounds 5 --samples 3 --output {output_path}",
        )

        # Verify the interactive display stages as they happen
        expect(term.get_by_text("Skill Tuner")).to_be_visible(timeout=30)
        expect(term.get_by_text("Round 1/")).to_be_visible(timeout=30)
        expect(term.get_by_text("Pass rate:")).to_be_visible(timeout=300)
        expect(term.get_by_text("Results saved to:")).to_be_visible(timeout=600)

        # Verify output file was created with expected structure
        assert output_path.exists(), f"Output file not found at {output_path}"

        tune_result = json.loads(output_path.read_text())

        assert "rounds" in tune_result, "Missing 'rounds' in result"
        assert len(tune_result["rounds"]) > 0, "No rounds in result"

        assert "result" in tune_result, "Missing 'result' in tune_result"
        final_pass_rate = tune_result["result"]["final_pass_rate"]
        assert final_pass_rate >= 80, (
            f"Final pass rate {final_pass_rate}% is too low. Expected at least 80%"
        )

        # Verify improvement of at least 40%
        # The pirate evals are calibrated: 001 passes (33%), 002 is 50/50, 003 fails
        # With 3 samples per eval, baseline is around 33-44%
        first_round_rate = tune_result["rounds"][0]["pass_rate"]
        improvement = final_pass_rate - first_round_rate
        assert improvement >= 40, (
            f"Improvement {improvement:.1f}% is too small. "
            f"Expected at least 40% improvement from {first_round_rate:.1f}% "
            f"to {final_pass_rate:.1f}%"
        )

        assert "best_skill" in tune_result, "Missing 'best_skill' in result"
        assert len(tune_result["best_skill"]) > 0, "best_skill is empty"

        updated_skill_content = skill_path.read_text().strip()
        assert updated_skill_content == tune_result["best_skill"].strip(), (
            "Skill file was not updated with best_skill content"
        )
