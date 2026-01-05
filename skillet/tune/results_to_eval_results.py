"""Convert raw eval results to EvalResult objects."""

from .result import EvalResult


def results_to_eval_results(results: list[dict]) -> list[EvalResult]:
    """Convert raw eval results to EvalResult objects."""
    return [
        EvalResult(
            source=r["eval_source"],
            passed=r["pass"],
            reasoning=r["judgment"].get("reasoning", ""),
            response=r.get("response"),
            tool_calls=r.get("tool_calls"),
        )
        for r in results
    ]
