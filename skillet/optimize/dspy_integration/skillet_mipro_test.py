"""Tests for SkilletMIPRO."""

from unittest.mock import MagicMock, patch

from skillet.optimize.dspy_integration.skillet_mipro import SkilletMIPRO


def _noop_init(_self, **_kwargs):
    """No-op init for patching MIPROv2 parent class."""
    pass


def describe_SkilletMIPRO():
    def describe_init():
        def it_stores_callbacks():
            on_start = MagicMock()
            on_complete = MagicMock()
            on_best = MagicMock()

            with patch.object(SkilletMIPRO, "__init__", _noop_init):
                mipro = SkilletMIPRO.__new__(SkilletMIPRO)
                mipro._on_trial_start = on_start
                mipro._on_trial_complete = on_complete
                mipro._on_new_best = on_best
                mipro._current_instruction_candidates = {}

            assert mipro._on_trial_start is on_start
            assert mipro._on_trial_complete is on_complete
            assert mipro._on_new_best is on_best

    def describe_get_current_instruction():
        def it_extracts_from_skill_module():
            with patch.object(SkilletMIPRO, "__init__", _noop_init):
                mipro = SkilletMIPRO.__new__(SkilletMIPRO)

            # Mock program with predictor.signature.instructions
            mock_program = MagicMock()
            mock_program.predictor.signature.instructions = "Be helpful"

            result = mipro._get_current_instruction(mock_program)
            assert result == "Be helpful"

        def it_extracts_from_named_predictors():
            with patch.object(SkilletMIPRO, "__init__", _noop_init):
                mipro = SkilletMIPRO.__new__(SkilletMIPRO)

            # Mock program without direct predictor
            mock_program = MagicMock()
            mock_program.predictor = None

            mock_module = MagicMock()
            mock_module.signature.instructions = "From named predictor"
            mock_program.named_predictors.return_value = [("pred", mock_module)]

            result = mipro._get_current_instruction(mock_program)
            assert result == "From named predictor"

        def it_returns_empty_on_error():
            with patch.object(SkilletMIPRO, "__init__", _noop_init):
                mipro = SkilletMIPRO.__new__(SkilletMIPRO)

            # Mock program that raises
            mock_program = MagicMock()
            mock_program.predictor.signature.instructions = None
            del mock_program.predictor

            result = mipro._get_current_instruction(mock_program)
            assert result == ""

        def it_handles_none_instructions():
            with patch.object(SkilletMIPRO, "__init__", _noop_init):
                mipro = SkilletMIPRO.__new__(SkilletMIPRO)

            mock_program = MagicMock()
            mock_program.predictor.signature.instructions = None

            result = mipro._get_current_instruction(mock_program)
            assert result == ""
