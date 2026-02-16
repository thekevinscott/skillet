"""Tests for skillet package lazy imports."""

import subprocess
import sys


def describe_lazy_imports():
    def it_does_not_import_dspy_eagerly():
        """import skillet should not trigger dspy import."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import skillet; import sys; print('dspy' in sys.modules)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "False", (
            f"dspy was imported eagerly. stderr: {result.stderr}"
        )

    def it_imports_tune_on_access():
        """Accessing skillet.tune should trigger the import."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import skillet; skillet.tune; import sys; print('dspy' in sys.modules)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "True"

    def it_raises_attribute_error_for_unknown():
        """Accessing unknown attribute should raise AttributeError."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import skillet; skillet.nonexistent_thing",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "AttributeError" in result.stderr
