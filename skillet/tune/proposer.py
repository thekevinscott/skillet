"""Instruction proposer using DSPy."""

from pathlib import Path

import dspy

from skillet.optimize import get_claude_lm

# Load proposer prompt from file
_PROPOSER_PROMPT_PATH = Path(__file__).parent / "proposer_prompt.txt"
_PROPOSER_PROMPT = _PROPOSER_PROMPT_PATH.read_text().strip()


def propose_instruction(
    current_instruction: str,
    trainset: list,
    failures: list[dict],
    instruction_history: list[dict],
) -> str:
    """Generate a new instruction using DSPy's proposal mechanism.

    Uses insights from MIPRO's grounded proposer to generate improved instructions
    based on the training data, failures, and previous attempts.

    Args:
        current_instruction: The current skill instruction text
        trainset: Training examples from evals
        failures: List of failed eval results
        instruction_history: Previous instruction attempts with scores

    Returns:
        Improved instruction text
    """
    # Build context for proposal
    failures_summary = "\n".join(
        [
            f"- Prompt: {f['prompt']}\n  Expected: {f['expected']}\n  Got: {f['response'][:200]}..."
            for f in failures[:3]  # Limit to 3 failures
        ]
    )

    history_summary = "\n".join(
        [
            f"- Score: {h['score']:.0%}\n  Instruction: {h['instruction'][:100]}..."
            for h in instruction_history[-3:]  # Last 3 attempts
        ]
    )

    examples_summary = "\n".join(
        [
            f"- Input: {ex.prompt}\n  Expected: {ex.expected}"
            for ex in trainset[:3]  # First 3 examples
        ]
    )

    # Use DSPy to generate improved instruction (scoped to avoid global state)
    with dspy.context(lm=get_claude_lm()):
        proposer = dspy.Predict(
            "current_instruction, failures, history, examples -> improved_instruction"
        )
        proposer.signature = proposer.signature.with_instructions(_PROPOSER_PROMPT)

        result = proposer(
            current_instruction=current_instruction,
            failures=failures_summary or "No failures to report",
            history=history_summary or "No previous attempts",
            examples=examples_summary,
        )

        return result.improved_instruction.strip()
