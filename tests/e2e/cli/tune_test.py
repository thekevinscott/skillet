"""End-to-end tests for the `skillet tune` command."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Paths to pirate test fixtures
PIRATE_FIXTURES = Path(__file__).parent.parent / "__fixtures__" / "tune-test"


def describe_skillet_tune():
    """Tests for the `skillet tune` command."""

    @pytest.mark.asyncio
    async def it_tunes_skill_to_target_pass_rate(tmp_path: Path):
        """Test that skillet tune improves a skill to reach target pass rate."""
        # Setup: Copy pirate fixtures to temp directory
        evals_dir = tmp_path / "evals" / "pirate"
        evals_dir.mkdir(parents=True)

        command_dir = tmp_path / ".claude" / "commands"
        command_dir.mkdir(parents=True)

        # Copy eval files
        pirate_evals = PIRATE_FIXTURES / "evals" / "pirate"
        for eval_file in pirate_evals.glob("*.yaml"):
            (evals_dir / eval_file.name).write_text(eval_file.read_text())

        # Copy command file
        pirate_command = PIRATE_FIXTURES / ".claude" / "commands" / "pirate.md"
        skill_path = command_dir / "pirate.md"
        skill_path.write_text(pirate_command.read_text())

        # Output path for results
        output_path = tmp_path / "tune_result.json"

        # Run CLI
        env = os.environ.copy()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skillet.cli.main",
                "tune",
                str(evals_dir),
                str(skill_path),
                "--target",
                "100",
                "--rounds",
                "5",
                "--samples",
                "3",
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=600,  # Allow time for multiple tune rounds
        )

        # Assertions
        assert result.returncode == 0, (
            f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Check output file was created
        assert output_path.exists(), f"Output file not found at {output_path}"

        # Verify result structure
        tune_result = json.loads(output_path.read_text())

        assert "rounds" in tune_result, "Missing 'rounds' in result"
        assert len(tune_result["rounds"]) > 0, "No rounds in result"

        # Check that pass rate improved or reached target
        assert "result" in tune_result, "Missing 'result' in tune_result"
        final_pass_rate = tune_result["result"]["final_pass_rate"]
        assert final_pass_rate >= 80, (
            f"Final pass rate {final_pass_rate}% is too low. Expected at least 80% (ideally 100%)"
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

        # Verify best_skill is populated
        assert "best_skill" in tune_result, "Missing 'best_skill' in result"
        assert len(tune_result["best_skill"]) > 0, "best_skill is empty"

        # Verify the skill file was updated with the best skill
        updated_skill_content = skill_path.read_text().strip()
        assert updated_skill_content == tune_result["best_skill"].strip(), (
            "Skill file was not updated with best_skill content"
        )
