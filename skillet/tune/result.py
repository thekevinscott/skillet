"""Tune result data structures."""

import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from skillet import __version__


@dataclass
class TuneConfig:
    """Configuration for a tune run."""

    num_trials: int
    optimizer: Literal["bootstrap", "mipro"]


@dataclass
class TuneMetadata:
    """Metadata about the tune run."""

    skillet_version: str = field(default_factory=lambda: __version__)
    python_version: str = field(
        default_factory=lambda: f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    platform: str = field(default_factory=platform.system)
    started_at: str = ""
    completed_at: str = ""
    eval_set: str = ""
    original_skill_path: str = ""


@dataclass
class TuneResultSummary:
    """Summary of tune results."""

    success: bool
    original_score: float
    optimized_score: float

    @property
    def improved(self) -> bool:
        """Whether optimization improved the score."""
        return self.optimized_score > self.original_score

    @property
    def delta(self) -> float:
        """Score improvement (positive = better)."""
        return self.optimized_score - self.original_score


@dataclass
class TuneResult:
    """Complete result of a tune run."""

    metadata: TuneMetadata
    config: TuneConfig
    result: TuneResultSummary
    original_skill: str
    optimized_skill: str

    @classmethod
    def create(
        cls,
        eval_set: str,
        skill_path: Path,
        original_skill: str,
        config: TuneConfig,
    ) -> "TuneResult":
        """Create a new TuneResult with initialized metadata."""
        return cls(
            metadata=TuneMetadata(
                started_at=datetime.now(UTC).isoformat(),
                eval_set=eval_set,
                original_skill_path=str(skill_path),
            ),
            config=config,
            result=TuneResultSummary(
                success=False,
                original_score=0.0,
                optimized_score=0.0,
            ),
            original_skill=original_skill,
            optimized_skill=original_skill,
        )

    def finalize(
        self,
        success: bool,
        original_score: float,
        optimized_score: float,
        optimized_skill: str,
    ) -> None:
        """Mark the tune run as complete with results."""
        self.metadata.completed_at = datetime.now(UTC).isoformat()
        self.result.success = success
        self.result.original_score = original_score
        self.result.optimized_score = optimized_score
        self.optimized_skill = optimized_skill

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Add computed properties
        data["result"]["improved"] = self.result.improved
        data["result"]["delta"] = self.result.delta
        return data

    def save(self, path: Path) -> None:
        """Save results to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "TuneResult":
        """Load results from a JSON file."""
        with path.open() as f:
            data = json.load(f)

        # Reconstruct nested dataclasses (ignore computed properties)
        result_data = data["result"]
        return cls(
            metadata=TuneMetadata(**data["metadata"]),
            config=TuneConfig(**data["config"]),
            result=TuneResultSummary(
                success=result_data["success"],
                original_score=result_data["original_score"],
                optimized_score=result_data["optimized_score"],
            ),
            original_skill=data["original_skill"],
            optimized_skill=data["optimized_skill"],
        )
