"""Tune result data structures."""

import json
import platform
import sys
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from skillet import __version__


@dataclass
class EvalResult:
    """Result of a single eval."""

    source: str
    passed: bool
    reasoning: str
    response: str | None = None
    tool_calls: list[dict] | None = None


@dataclass
class RoundResult:
    """Result of a single tuning round."""

    round: int
    pass_rate: float
    skill_content: str
    tip_used: str | None
    evals: list[EvalResult]


@dataclass
class TuneConfig:
    """Configuration for a tune run."""

    max_rounds: int = 5
    target_pass_rate: float = 100.0
    samples: int = 1
    parallel: int = 3


@dataclass
class TuneCallbacks:
    """Callbacks for tune progress reporting."""

    on_round_start: Callable[[int, int], Awaitable[None]] | None = None
    """Called when a round starts. Args: (round_num, total_rounds)"""

    on_eval_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None
    """Called for eval status updates. Args: (task, status, result)"""

    on_round_complete: Callable[[int, float, list[dict]], Awaitable[None]] | None = None
    """Called when a round completes. Args: (round_num, pass_rate, results)"""

    on_improving: Callable[[str], Awaitable[None]] | None = None
    """Called when optimization starts. Args: (message,)"""

    on_improved: Callable[[str, Path], Awaitable[None]] | None = None
    """Called when skill improved. Args: (instruction, save_path)"""

    on_complete: Callable[[Path], Awaitable[None]] | None = None
    """Called when tuning completes. Args: (save_path,)"""


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
    final_pass_rate: float
    rounds_completed: int
    best_round: int


@dataclass
class TuneResult:
    """Complete result of a tune run."""

    metadata: TuneMetadata
    config: TuneConfig
    result: TuneResultSummary
    original_skill: str
    best_skill: str
    rounds: list[RoundResult] = field(default_factory=list)

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
                final_pass_rate=0.0,
                rounds_completed=0,
                best_round=0,
            ),
            original_skill=original_skill,
            best_skill=original_skill,
            rounds=[],
        )

    def add_round(self, round_result: RoundResult) -> None:
        """Add a round result and update best if needed."""
        self.rounds.append(round_result)
        self.result.rounds_completed = len(self.rounds)

        # Update best if this round has highest pass rate
        if round_result.pass_rate >= self.result.final_pass_rate:
            self.result.final_pass_rate = round_result.pass_rate
            self.result.best_round = round_result.round
            self.best_skill = round_result.skill_content

    def finalize(self, success: bool) -> None:
        """Mark the tune run as complete."""
        self.metadata.completed_at = datetime.now(UTC).isoformat()
        self.result.success = success

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

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

        # Reconstruct nested dataclasses
        return cls(
            metadata=TuneMetadata(**data["metadata"]),
            config=TuneConfig(**data["config"]),
            result=TuneResultSummary(**data["result"]),
            original_skill=data["original_skill"],
            best_skill=data["best_skill"],
            rounds=[
                RoundResult(
                    round=r["round"],
                    pass_rate=r["pass_rate"],
                    skill_content=r["skill_content"],
                    tip_used=r["tip_used"],
                    evals=[EvalResult(**e) for e in r["evals"]],
                )
                for r in data["rounds"]
            ],
        )
