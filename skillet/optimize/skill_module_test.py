"""Tests for skillet.optimize.skill_module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import dspy

from skillet.optimize.skill_module import SkillModule


def describe_skill_module():
    """Tests for SkillModule class."""

    def describe_init():
        """Tests for __init__."""

        def it_stores_skill_content():
            """Should store the skill content."""
            content = "Test skill instructions"
            module = SkillModule(content)
            assert module.skill_content == content

        def it_creates_predictor():
            """Should create a DSPy predictor."""
            module = SkillModule("Test instructions")
            assert hasattr(module, "predictor")
            assert isinstance(module.predictor, dspy.Predict)

        def it_sets_instructions_on_signature():
            """Should set skill content as signature instructions."""
            content = "Do something specific"
            module = SkillModule(content)
            assert module.predictor.signature.instructions == content

    def describe_forward():
        """Tests for forward method."""

        @patch.object(dspy.Predict, "__call__")
        def it_calls_predictor_with_prompt(mock_call: MagicMock):
            """Should call predictor with the prompt."""
            mock_call.return_value = dspy.Prediction(response="test response")

            module = SkillModule("Test instructions")
            module.forward(prompt="test prompt")

            mock_call.assert_called_once_with(prompt="test prompt")

        @patch.object(dspy.Predict, "__call__")
        def it_returns_prediction(mock_call: MagicMock):
            """Should return DSPy Prediction."""
            expected = dspy.Prediction(response="test response")
            mock_call.return_value = expected

            module = SkillModule("Test instructions")
            result = module.forward(prompt="test")

            assert result == expected

    def describe_from_file():
        """Tests for from_file class method."""

        def it_loads_from_md_file():
            """Should load skill from .md file."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write("# Test Skill\nDo something")
                f.flush()

                module = SkillModule.from_file(f.name)

                assert module.skill_content == "# Test Skill\nDo something"

        def it_loads_from_directory_with_skill_md():
            """Should load SKILL.md from directory."""
            with tempfile.TemporaryDirectory() as tmpdir:
                skill_file = Path(tmpdir) / "SKILL.md"
                skill_file.write_text("# Directory Skill\nInstructions here")

                module = SkillModule.from_file(tmpdir)

                assert module.skill_content == "# Directory Skill\nInstructions here"

        def it_accepts_path_object():
            """Should accept Path objects."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write("Path skill content")
                f.flush()

                module = SkillModule.from_file(Path(f.name))

                assert module.skill_content == "Path skill content"

    def describe_get_optimized_skill():
        """Tests for get_optimized_skill method."""

        def it_returns_current_instructions():
            """Should return current signature instructions."""
            module = SkillModule("Original instructions")

            result = module.get_optimized_skill()

            assert result == "Original instructions"

        def it_reflects_modified_instructions():
            """Should reflect any modifications to signature instructions."""
            module = SkillModule("Original")

            # Simulate what an optimizer might do
            module.predictor.signature = module.predictor.signature.with_instructions(
                "Optimized instructions"
            )

            result = module.get_optimized_skill()

            assert result == "Optimized instructions"
