"""Load evals as DSPy training data."""

import dspy


def evals_to_trainset(evals: list[dict]) -> list[dspy.Example]:
    """Convert skillet evals to DSPy training examples."""
    return [
        dspy.Example(prompt=eval_data["prompt"], expected=eval_data["expected"]).with_inputs(
            "prompt"
        )
        for eval_data in evals
    ]
