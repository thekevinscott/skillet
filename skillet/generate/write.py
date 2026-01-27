"""Write candidate evals to YAML files."""

from datetime import UTC, datetime
from pathlib import Path

import yaml

from .sanitize_filename import get_name_part
from .types import CandidateEval


def write_candidates(
    candidates: list[CandidateEval],
    output_dir: Path,
    *,
    skill_name: str | None = None,
) -> list[Path]:
    """Write candidate evals to YAML files in output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths = []
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    for i, candidate in enumerate(candidates):
        name_part = get_name_part(candidate.name, i)
        filepath = output_dir / f"{name_part}.yaml"

        # Handle name collisions
        if filepath.exists():
            filepath = output_dir / f"{name_part}-{timestamp}-{i + 1}.yaml"

        # Build YAML content
        data = _candidate_to_dict(candidate, skill_name)

        # Write with comments
        content = _format_yaml_with_comments(data, candidate)
        filepath.write_text(content)

        written_paths.append(filepath)

    return written_paths


def _candidate_to_dict(candidate: CandidateEval, skill_name: str | None) -> dict:
    """Convert candidate to dict for YAML serialization."""
    data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "prompt": candidate.prompt,
        "expected": candidate.expected,
        "name": candidate.name,
    }

    # Add metadata as comments (stored in _meta for reference)
    meta = {
        "category": candidate.category,
        "source": candidate.source,
        "confidence": candidate.confidence,
        "rationale": candidate.rationale,
        "generated": True,
    }
    if skill_name:
        meta["skill_name"] = skill_name
    data["_meta"] = meta

    return data


def _format_yaml_with_comments(data: dict, candidate: CandidateEval) -> str:
    """Format YAML with helpful comments."""
    # Add header comment
    lines = [
        "# Generated eval candidate",
        f"# Category: {candidate.category}",
        f"# Source: {candidate.source}",
        f"# Confidence: {candidate.confidence:.0%}",
        f"# Rationale: {candidate.rationale}",
        "#",
        "# Review and edit before using in evaluations.",
        "# Remove _meta section after review.",
        "",
    ]

    # Serialize without the _meta for cleaner output
    clean_data = {k: v for k, v in data.items() if k != "_meta"}
    yaml_content = yaml.dump(
        clean_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    lines.append(yaml_content)

    # Add _meta as comment block
    lines.extend(
        [
            "",
            "# Metadata (remove after review):",
        ]
    )
    meta_yaml = yaml.dump(
        {"_meta": data["_meta"]},
        default_flow_style=False,
        allow_unicode=True,
    )
    for line in meta_yaml.strip().split("\n"):
        lines.append(f"# {line}")

    return "\n".join(lines)
