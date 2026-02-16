"""Create skill result data structures."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CreateSkillResult:
    """Complete result of a create_skill() call."""

    skill_dir: Path
    skill_content: str
    eval_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        d["skill_dir"] = self.skill_dir
        return d
