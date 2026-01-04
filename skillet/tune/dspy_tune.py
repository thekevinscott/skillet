"""DSPy-powered tuning using MIPROv2 for instruction optimization.

This module uses DSPy's MIPROv2 to generate and optimize instruction candidates,
but uses Skillet's native eval system (Claude Agent SDK) to measure pass rates.
This gives us the best of both worlds:
- MIPRO's systematic instruction generation and Bayesian optimization
- Skillet's accurate eval measurement via Claude Code
"""

import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

import dspy

from skillet.evals import load_evals
from skillet.optimize import evals_to_trainset, get_claude_lm

from .improve import get_skill_file
from .result import EvalResult, RoundResult, TuneConfig, TuneResult
from .run import run_tune_eval


def _results_to_eval_results(results: list[dict]) -> list[EvalResult]:
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


async def tune_dspy(  # noqa: PLR0913
    name: str,
    skill_path: Path,
    max_rounds: int = 5,
    target_pass_rate: float = 100.0,
    samples: int = 1,
    parallel: int = 3,
    on_round_start: Callable[[int, int], Awaitable[None]] | None = None,
    on_eval_status: Callable[[dict, str, dict | None], Awaitable[None]] | None = None,
    on_round_complete: Callable[[int, float, list[dict]], Awaitable[None]] | None = None,
    on_improving: Callable[[str], Awaitable[None]] | None = None,
    on_improved: Callable[[str, Path], Awaitable[None]] | None = None,
    on_complete: Callable[[Path], Awaitable[None]] | None = None,
) -> TuneResult:
    """Tune a skill using DSPy's MIPROv2-inspired instruction generation.

    Uses DSPy's GroundedProposer to generate instruction candidates based on:
    - The current skill content
    - Training examples from evals
    - Previous instruction attempts with their scores

    But uses Skillet's native eval system (Claude Agent SDK) to measure pass rates,
    ensuring accurate measurement of how the skill performs in Claude Code.

    Args:
        name: Name of eval set (path to evals directory)
        skill_path: Path to skill file or directory
        max_rounds: Maximum optimization rounds
        target_pass_rate: Target pass rate percentage
        samples: Number of samples per eval
        parallel: Number of parallel workers
        on_round_start: Callback when round starts (round_num, total_rounds)
        on_eval_status: Callback for eval status updates (task, status, result)
        on_round_complete: Callback when round completes (round_num, score, results)
        on_improving: Callback when optimization starts (message)
        on_improved: Callback when skill improved and saved (instruction, save_path)
        on_complete: Callback when tuning completes (save_path)

    Returns:
        TuneResult with all rounds and the best skill content
    """
    # Load skill and evals
    original_skill_file = get_skill_file(skill_path)
    original_skill_content = original_skill_file.read_text()
    evals = load_evals(name)
    trainset = evals_to_trainset(name)

    # Create result tracker
    tune_result = TuneResult.create(
        eval_set=name,
        skill_path=skill_path,
        original_skill=original_skill_content,
        config=TuneConfig(
            max_rounds=max_rounds,
            target_pass_rate=target_pass_rate,
            samples=samples,
            parallel=parallel,
        ),
    )

    # Create temporary directory for skill iterations
    with tempfile.TemporaryDirectory(prefix="skillet-tune-dspy-") as temp_dir:
        # Set up temp skill path
        if ".claude" in skill_path.parts:
            claude_idx = skill_path.parts.index(".claude")
            relative_path = Path(*skill_path.parts[claude_idx:])
            temp_skill_path = Path(temp_dir) / relative_path
        else:
            temp_skill_path = Path(temp_dir) / original_skill_file.name

        temp_skill_path.parent.mkdir(parents=True, exist_ok=True)
        temp_skill_path.write_text(original_skill_content)

        current_skill_content = original_skill_content
        instruction_history: list[dict] = []

        for round_num in range(1, max_rounds + 1):
            if on_round_start:
                await on_round_start(round_num, max_rounds)

            # Run evals using our native eval system
            pass_rate, results = await run_tune_eval(
                evals, temp_skill_path, samples, parallel, on_eval_status
            )

            # Record this round
            round_result = RoundResult(
                round=round_num,
                pass_rate=pass_rate,
                skill_content=current_skill_content,
                tip_used="DSPy GroundedProposer",
                evals=_results_to_eval_results(results),
            )
            tune_result.add_round(round_result)

            # Track for instruction proposal
            instruction_history.append({
                "instruction": current_skill_content,
                "score": pass_rate / 100,  # Normalize to 0-1
            })

            if on_round_complete:
                await on_round_complete(round_num, pass_rate, results)

            if pass_rate >= target_pass_rate:
                tune_result.finalize(success=True)
                # Save final skill and notify
                original_skill_file.write_text(tune_result.best_skill + "\n")
                if on_complete:
                    await on_complete(original_skill_file)
                return tune_result

            # Generate new instruction using DSPy's proposal mechanism
            if on_improving:
                await on_improving("Improving skill...")

            new_instruction = _propose_instruction(
                current_instruction=current_skill_content,
                trainset=trainset,
                failures=[r for r in results if not r["pass"]],
                instruction_history=instruction_history,
            )

            current_skill_content = new_instruction
            temp_skill_path.write_text(new_instruction + "\n")

            # Save improved skill to original file (for interrupt safety)
            original_skill_file.write_text(new_instruction + "\n")

            if on_improved:
                await on_improved(new_instruction, original_skill_file)

        tune_result.finalize(success=False)
        # Save best skill and notify
        original_skill_file.write_text(tune_result.best_skill + "\n")
        if on_complete:
            await on_complete(original_skill_file)
        return tune_result


def _propose_instruction(
    current_instruction: str,
    trainset: list,
    failures: list[dict],
    instruction_history: list[dict],
) -> str:
    """Generate a new instruction using DSPy's proposal mechanism.

    Uses insights from MIPRO's grounded proposer to generate improved instructions
    based on the training data, failures, and previous attempts.
    """
    # Build context for proposal
    failures_summary = "\n".join([
        f"- Prompt: {f['prompt']}\n  Expected: {f['expected']}\n  Got: {f['response'][:200]}..."
        for f in failures[:3]  # Limit to 3 failures
    ])

    history_summary = "\n".join([
        f"- Score: {h['score']:.0%}\n  Instruction: {h['instruction'][:100]}..."
        for h in instruction_history[-3:]  # Last 3 attempts
    ])

    examples_summary = "\n".join([
        f"- Input: {ex.prompt}\n  Expected: {ex.expected}"
        for ex in trainset[:3]  # First 3 examples
    ])

    # Use DSPy to generate improved instruction (scoped to avoid global state)
    with dspy.context(lm=get_claude_lm()):
        proposer = dspy.Predict(
            "current_instruction, failures, history, examples -> improved_instruction"
        )
        proposer.signature = proposer.signature.with_instructions("""
You are an expert prompt engineer optimizing instructions for a Claude Code skill.

Given the current instruction, examples of failures, previous attempts with scores,
and training examples, generate an improved instruction that:
1. Addresses the specific failures observed
2. Builds on what worked in previous attempts
3. Is clear, specific, and actionable
4. Uses imperative language (DO this, NEVER do that)
5. Keeps the instruction concise but complete

Return ONLY the improved instruction text, no explanations.
""")

        result = proposer(
            current_instruction=current_instruction,
            failures=failures_summary or "No failures to report",
            history=history_summary or "No previous attempts",
            examples=examples_summary,
        )

        return result.improved_instruction.strip()
