"""DSPy module wrapper for Skillet skills."""

from pathlib import Path

import dspy


class SkillModule(dspy.Module):
    """DSPy module that wraps a skill's instructions.

    Allows DSPy optimizers to tune skill content by treating it
    as optimizable instructions for a signature.

    Example:
        skill = SkillModule.from_file("path/to/skill")
        result = skill(prompt="user input")
        optimized = skill.get_optimized_skill()
    """

    def __init__(self, skill_content: str):
        """Initialize with skill content.

        Args:
            skill_content: The skill instructions (SKILL.md content)
        """
        super().__init__()
        self.skill_content = skill_content

        # Create a predictor with skill content as instructions
        self.predictor = dspy.Predict("prompt -> response")
        # Inject skill content as the signature instructions
        self.predictor.signature = self.predictor.signature.with_instructions(skill_content)

    def forward(self, prompt: str) -> dspy.Prediction:
        """Run the skill predictor.

        Args:
            prompt: Input prompt to process

        Returns:
            DSPy Prediction with response field
        """
        return self.predictor(prompt=prompt)

    @classmethod
    def from_file(cls, skill_path: Path | str) -> "SkillModule":
        """Load skill from a file or directory.

        Args:
            skill_path: Path to skill directory (with SKILL.md) or direct .md file

        Returns:
            SkillModule instance
        """
        path = Path(skill_path)
        skill_file = path / "SKILL.md" if path.is_dir() else path
        return cls(skill_content=skill_file.read_text())

    def get_optimized_skill(self) -> str:
        """Extract optimized instructions after optimization.

        Returns:
            The current instructions from the predictor's signature
        """
        return self.predictor.signature.instructions
