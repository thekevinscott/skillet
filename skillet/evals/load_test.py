"""Tests for evals/load module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.errors import EmptyFolderError, EvalValidationError
from skillet.evals.load import load_evals, validate_eval


def describe_validate_eval():
    """Tests for validate_eval function."""

    def it_passes_for_valid_eval():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test prompt",
            "expected": "expected response",
            "name": "test-eval",
        }
        # Should not raise
        validate_eval(eval_data, "test.yaml")

    def it_raises_for_non_dict():
        with pytest.raises(EvalValidationError, match="not a valid YAML dictionary"):
            validate_eval("not a dict", "test.yaml")  # type: ignore[arg-type]

    def it_raises_for_missing_fields():
        eval_data = {"prompt": "test"}  # missing timestamp, expected, name
        with pytest.raises(EvalValidationError, match="missing required fields"):
            validate_eval(eval_data, "test.yaml")

    def it_includes_missing_field_names_in_error():
        eval_data = {"prompt": "test", "timestamp": "2024-01-01"}
        with pytest.raises(EvalValidationError, match="expected") as exc_info:
            validate_eval(eval_data, "test.yaml")
        assert "name" in str(exc_info.value)


def describe_load_evals():
    """Tests for load_evals function."""

    def it_loads_single_yaml_file():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.yaml"
            path.write_text(
                "timestamp: 2024-01-01\n"
                "prompt: test prompt\n"
                "expected: expected response\n"
                "name: test-eval\n"
            )
            result = load_evals(str(path))
            assert len(result) == 1
            assert result[0]["prompt"] == "test prompt"
            assert result[0]["_source"] == path.name
            assert "_content" in result[0]

    def it_raises_for_non_yaml_file():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("not yaml")
            with pytest.raises(EvalValidationError, match=r"Expected \.yaml file"):
                load_evals(str(path))

    def it_loads_directory_of_evals():
        with tempfile.TemporaryDirectory() as tmpdir:
            evals_dir = Path(tmpdir)
            (evals_dir / "001.yaml").write_text(
                "timestamp: 2024-01-01\n"
                "prompt: first prompt\n"
                "expected: first response\n"
                "name: first-eval\n"
            )
            (evals_dir / "002.yaml").write_text(
                "timestamp: 2024-01-02\n"
                "prompt: second prompt\n"
                "expected: second response\n"
                "name: second-eval\n"
            )

            result = load_evals(tmpdir)
            assert len(result) == 2
            # Should be sorted
            assert result[0]["_source"] == "001.yaml"
            assert result[1]["_source"] == "002.yaml"

    def it_loads_nested_subdirectories():
        with tempfile.TemporaryDirectory() as tmpdir:
            evals_dir = Path(tmpdir)
            subdir = evals_dir / "subdir"
            subdir.mkdir()

            (evals_dir / "root.yaml").write_text(
                "timestamp: 2024-01-01\n"
                "prompt: root prompt\n"
                "expected: root response\n"
                "name: root-eval\n"
            )
            (subdir / "nested.yaml").write_text(
                "timestamp: 2024-01-02\n"
                "prompt: nested prompt\n"
                "expected: nested response\n"
                "name: nested-eval\n"
            )

            result = load_evals(tmpdir)
            assert len(result) == 2
            sources = [r["_source"] for r in result]
            assert "root.yaml" in sources
            assert "subdir/nested.yaml" in sources

    def it_raises_for_nonexistent_directory():
        with pytest.raises(EmptyFolderError, match="No evals found"):
            load_evals("nonexistent-dir-12345")

    def it_raises_for_empty_directory():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            pytest.raises(EmptyFolderError, match="No eval files found"),
        ):
            load_evals(tmpdir)

    def it_raises_for_invalid_eval_in_directory():
        with tempfile.TemporaryDirectory() as tmpdir:
            evals_dir = Path(tmpdir)
            (evals_dir / "invalid.yaml").write_text("just: incomplete")

            with pytest.raises(EvalValidationError, match="missing required fields"):
                load_evals(tmpdir)

    def it_raises_when_evals_subpath_is_file():
        """Test error when ~/.skillet/evals/<name> exists but is a file, not a directory."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.evals.load.SKILLET_DIR", Path(tmpdir)),
        ):
            evals_dir = Path(tmpdir) / "evals"
            evals_dir.mkdir()
            # Create a file where we expect a directory
            (evals_dir / "my-evals").write_text("not a directory")

            with pytest.raises(EmptyFolderError, match="Not a directory"):
                load_evals("my-evals")
