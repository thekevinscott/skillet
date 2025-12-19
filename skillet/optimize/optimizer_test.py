"""Tests for skillet.optimize.optimizer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from skillet.optimize.optimizer import optimize_skill


def describe_optimize_skill():
    """Tests for optimize_skill function."""

    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    def it_loads_skill_from_path(mock_skill_module, mock_evals_to_trainset):
        """Should load skill from the provided path."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "optimized"
        mock_skill_module.from_file.return_value = mock_module
        mock_evals_to_trainset.return_value = []

        # Create mock optimizer
        mock_optimizer = MagicMock()
        mock_optimizer.compile.return_value = mock_module

        optimize_skill(
            skill_path="/path/to/skill",
            eval_name="test-evals",
            optimizer=mock_optimizer,
        )

        mock_skill_module.from_file.assert_called_once_with("/path/to/skill")

    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    def it_loads_evals_as_trainset(mock_skill_module, mock_evals_to_trainset):
        """Should load evals and convert to trainset."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "optimized"
        mock_skill_module.from_file.return_value = mock_module
        mock_evals_to_trainset.return_value = []

        mock_optimizer = MagicMock()
        mock_optimizer.compile.return_value = mock_module

        optimize_skill(
            skill_path="/path/to/skill",
            eval_name="my-evals",
            optimizer=mock_optimizer,
        )

        mock_evals_to_trainset.assert_called_once_with("my-evals")

    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    def it_compiles_with_optimizer(mock_skill_module, mock_evals_to_trainset):
        """Should call optimizer.compile with skill and trainset."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "optimized"
        mock_skill_module.from_file.return_value = mock_module

        trainset = [MagicMock(), MagicMock()]
        mock_evals_to_trainset.return_value = trainset

        mock_optimizer = MagicMock()
        mock_optimizer.compile.return_value = mock_module

        optimize_skill(
            skill_path="/path/to/skill",
            eval_name="test",
            optimizer=mock_optimizer,
        )

        mock_optimizer.compile.assert_called_once_with(mock_module, trainset=trainset)

    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    def it_returns_optimized_skill_content(mock_skill_module, mock_evals_to_trainset):
        """Should return the optimized skill content."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "# Optimized Skill\nNew instructions"
        mock_skill_module.from_file.return_value = mock_module
        mock_evals_to_trainset.return_value = []

        mock_optimizer = MagicMock()
        mock_optimizer.compile.return_value = mock_module

        result = optimize_skill(
            skill_path="/path/to/skill",
            eval_name="test",
            optimizer=mock_optimizer,
        )

        assert result == "# Optimized Skill\nNew instructions"

    @patch("skillet.optimize.optimizer.create_skillet_metric")
    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    @patch("skillet.optimize.optimizer.dspy.BootstrapFewShot")
    def it_uses_default_optimizer_when_none_provided(
        mock_bootstrap, mock_skill_module, mock_evals_to_trainset, mock_create_metric
    ):
        """Should use BootstrapFewShot by default."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "optimized"
        mock_skill_module.from_file.return_value = mock_module
        mock_evals_to_trainset.return_value = []

        mock_metric = MagicMock()
        mock_create_metric.return_value = mock_metric

        mock_optimizer_instance = MagicMock()
        mock_optimizer_instance.compile.return_value = mock_module
        mock_bootstrap.return_value = mock_optimizer_instance

        optimize_skill(
            skill_path="/path/to/skill",
            eval_name="test",
            optimizer=None,
        )

        mock_create_metric.assert_called_once()
        mock_bootstrap.assert_called_once_with(metric=mock_metric)

    @patch("skillet.optimize.optimizer.evals_to_trainset")
    @patch("skillet.optimize.optimizer.SkillModule")
    def it_accepts_path_object(mock_skill_module, mock_evals_to_trainset):
        """Should accept Path objects for skill_path."""
        mock_module = MagicMock()
        mock_module.get_optimized_skill.return_value = "optimized"
        mock_skill_module.from_file.return_value = mock_module
        mock_evals_to_trainset.return_value = []

        mock_optimizer = MagicMock()
        mock_optimizer.compile.return_value = mock_module

        path = Path("/path/to/skill")
        optimize_skill(
            skill_path=path,
            eval_name="test",
            optimizer=mock_optimizer,
        )

        mock_skill_module.from_file.assert_called_once_with(path)
