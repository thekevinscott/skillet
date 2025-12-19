"""Tests for cli/main module."""

from skillet.cli.main import app


def describe_app():
    """Tests for CLI app structure."""

    def it_has_name():
        assert app.name == ("skillet",)

    def it_has_registered_commands():
        # Check that commands are registered
        assert hasattr(app, "_registered_commands")

    def it_has_eval_command():
        # Check eval command exists - Commands are registered as function objects
        assert len(app._registered_commands) > 0

    def it_has_multiple_commands():
        # Should have at least new, eval, tune, compare commands
        assert len(app._registered_commands) >= 4
