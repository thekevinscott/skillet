"""Load evals as DSPy training data."""

import dspy

from skillet.evals import load_evals


def evals_to_trainset(name: str) -> list[dspy.Example]:
    """Convert skillet evals to DSPy training examples.

    Args:
        name: Eval name/path (same format as load_evals)

    Returns:
        List of DSPy Examples with prompt as input field and expected as label

    Example:
        trainset = evals_to_trainset("add-command")
        for example in trainset:
            print(example.prompt, "->", example.expected)
    """
    evals = load_evals(name)

    return [
        dspy.Example(prompt=eval_data["prompt"], expected=eval_data["expected"]).with_inputs(
            "prompt"
        )
        for eval_data in evals
    ]
