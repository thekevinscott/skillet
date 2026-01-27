"""Tests for write module."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from skillet.evals.load import load_evals

from .types import CandidateEval
from .write import _candidate_to_dict, _format_yaml_with_comments, write_candidates

FIXED_DT = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)


def _make_candidate(**overrides: object) -> CandidateEval:
    defaults = {
        "prompt": "What is 2+2?",
        "expected": "4",
        "name": "basic-math",
        "category": "positive",
        "source": "goal:1",
        "confidence": 0.85,
        "rationale": "Tests basic arithmetic",
    }
    defaults.update(overrides)
    return CandidateEval(**defaults)  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def _freeze_time():
    with patch("skillet.generate.write.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_DT
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        yield mock_dt


def describe_candidate_to_dict():
    def it_includes_all_required_fields():
        result = _candidate_to_dict(_make_candidate(), None)
        assert {"timestamp", "prompt", "expected", "name"} <= set(result)

    def it_uses_candidate_name_not_skill_name():
        result = _candidate_to_dict(_make_candidate(name="my-eval"), "some-skill")
        assert result["name"] == "my-eval"

    def it_includes_meta_fields():
        result = _candidate_to_dict(_make_candidate(), None)
        meta = result["_meta"]
        assert meta["category"] == "positive"
        assert meta["source"] == "goal:1"
        assert meta["confidence"] == 0.85
        assert meta["rationale"] == "Tests basic arithmetic"
        assert meta["generated"] is True

    def it_adds_skill_name_to_meta_when_provided():
        result = _candidate_to_dict(_make_candidate(), "my-skill")
        assert result["_meta"]["skill_name"] == "my-skill"

    def it_omits_skill_name_from_meta_when_none():
        result = _candidate_to_dict(_make_candidate(), None)
        assert "skill_name" not in result["_meta"]

    def it_uses_frozen_timestamp():
        result = _candidate_to_dict(_make_candidate(), None)
        assert result["timestamp"] == FIXED_DT.isoformat()


def describe_format_yaml_with_comments():
    def it_starts_with_header_comment():
        data = _candidate_to_dict(_make_candidate(), None)
        output = _format_yaml_with_comments(data, _make_candidate())
        assert output.startswith("# Generated eval candidate")

    def it_includes_confidence_as_percentage():
        data = _candidate_to_dict(_make_candidate(confidence=0.85), None)
        output = _format_yaml_with_comments(data, _make_candidate(confidence=0.85))
        assert "# Confidence: 85%" in output

    def it_produces_parseable_yaml_body():
        data = _candidate_to_dict(_make_candidate(), None)
        output = _format_yaml_with_comments(data, _make_candidate())
        body = "\n".join(line for line in output.split("\n") if line and not line.startswith("#"))
        parsed = yaml.safe_load(body)
        assert parsed["prompt"] == "What is 2+2?"
        assert parsed["expected"] == "4"

    def it_excludes_meta_from_yaml_body():
        data = _candidate_to_dict(_make_candidate(), None)
        output = _format_yaml_with_comments(data, _make_candidate())
        body = "\n".join(line for line in output.split("\n") if line and not line.startswith("#"))
        parsed = yaml.safe_load(body)
        assert "_meta" not in parsed

    def it_includes_meta_as_comments():
        data = _candidate_to_dict(_make_candidate(), None)
        output = _format_yaml_with_comments(data, _make_candidate())
        assert "# _meta:" in output
        assert "# Metadata (remove after review):" in output


def describe_write_candidates():
    def it_creates_output_dir(tmp_path: Path):
        out = tmp_path / "new" / "nested"
        write_candidates([], out)
        assert out.is_dir()

    def it_writes_one_file_per_candidate(tmp_path: Path):
        candidates = [_make_candidate(name=f"eval-{i}") for i in range(3)]
        paths = write_candidates(candidates, tmp_path)
        assert len(paths) == 3
        assert all(p.exists() for p in paths)

    def it_uses_sanitized_name_for_filename(tmp_path: Path):
        paths = write_candidates([_make_candidate(name="my eval/test")], tmp_path)
        assert paths[0].name == "my-eval-test.yaml"

    def it_writes_valid_yaml(tmp_path: Path):
        paths = write_candidates([_make_candidate()], tmp_path)
        body = "\n".join(
            line for line in paths[0].read_text().split("\n") if line and not line.startswith("#")
        )
        parsed = yaml.safe_load(body)
        assert parsed["prompt"] == "What is 2+2?"

    def it_writes_files_loadable_by_load_evals(tmp_path: Path):
        paths = write_candidates(
            [_make_candidate(name="loadable")], tmp_path, skill_name="test-skill"
        )
        loaded = load_evals(str(paths[0]))
        assert len(loaded) == 1
        assert loaded[0]["prompt"] == "What is 2+2?"
        assert loaded[0]["name"] == "loadable"
