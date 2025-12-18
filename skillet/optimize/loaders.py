"""Convert skillet evals to DSPy Examples."""

import dspy

from skillet.gaps import load_gaps


def evals_to_trainset(name: str) -> list[dspy.Example]:
    """Convert skillet evals to DSPy training examples.

    Args:
        name: Eval set name or path (same as load_gaps)

    Returns:
        List of DSPy Examples with 'prompt' and 'expected' as inputs
    """
    evals = load_gaps(name)

    trainset = []
    for eval_data in evals:
        example = dspy.Example(
            prompt=eval_data["prompt"],
            expected=eval_data["expected"],
            source=eval_data.get("_source", ""),
        ).with_inputs("prompt")
        trainset.append(example)

    return trainset
