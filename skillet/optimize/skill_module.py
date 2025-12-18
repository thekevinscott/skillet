"""DSPy module for skill-guided Claude responses."""

from pathlib import Path

import dspy


class SkillSignature(dspy.Signature):
    """Generate a response following the skill instructions."""

    prompt: str = dspy.InputField(desc="The user's prompt")
    response: str = dspy.OutputField(desc="Claude's response following the skill")


class SkillModule(dspy.Module):
    """DSPy module that wraps skill execution.

    This module uses a skill (system prompt) to guide Claude's responses.
    The skill text is what gets optimized by DSPy.
    """

    def __init__(self, skill_content: str):
        """Initialize with skill content.

        Args:
            skill_content: The skill markdown content (system prompt)
        """
        super().__init__()
        self.skill_content = skill_content
        # Create a predictor with instructions from the skill
        self.predictor = dspy.Predict(SkillSignature)
        # Inject skill as the signature instructions
        self.predictor.signature = self.predictor.signature.with_instructions(skill_content)

    def forward(self, prompt: str) -> dspy.Prediction:
        """Run the skill-guided prediction.

        Args:
            prompt: User prompt to respond to

        Returns:
            DSPy Prediction with response field
        """
        return self.predictor(prompt=prompt)

    @classmethod
    def from_file(cls, skill_path: Path) -> "SkillModule":
        """Create a SkillModule from a skill file.

        Args:
            skill_path: Path to skill .md file or directory with SKILL.md

        Returns:
            SkillModule instance
        """
        skill_file = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
        skill_content = skill_file.read_text()
        return cls(skill_content)

    def get_optimized_skill(self) -> str:
        """Extract the optimized skill content after DSPy optimization.

        Returns:
            The optimized instruction text
        """
        return self.predictor.signature.instructions
