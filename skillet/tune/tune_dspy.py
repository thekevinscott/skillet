"""DSPy-powered tuning using MIPROv2 for instruction optimization.

This module uses DSPy's MIPROv2 to generate and optimize instruction candidates,
but uses Skillet's native eval system (Claude Agent SDK) to measure pass rates.
This gives us the best of both worlds:
- MIPRO's systematic instruction generation and Bayesian optimization
- Skillet's accurate eval measurement via Claude Code
"""

import tempfile
from pathlib import Path

from skillet.evals import load_evals
from skillet.optimize import evals_to_trainset

from .improve import get_skill_file
from .proposer import propose_instruction
from .result import (
    RoundResult,
    TuneCallbacks,
    TuneConfig,
    TuneResult,
)
from .results_to_eval_results import results_to_eval_results
from .run import run_tune_eval


async def tune_dspy(
    name: str,
    skill_path: Path,
    config: TuneConfig | None = None,
    callbacks: TuneCallbacks | None = None,
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
        config: Tuning configuration (max_rounds, target_pass_rate, samples, parallel)
        callbacks: Progress callbacks for UI updates

    Returns:
        TuneResult with all rounds and the best skill content
    """
    # Use defaults if not provided
    config = config or TuneConfig()
    callbacks = callbacks or TuneCallbacks()

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
        config=config,
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

        for round_num in range(1, config.max_rounds + 1):
            if callbacks.on_round_start:
                await callbacks.on_round_start(round_num, config.max_rounds)

            # Run evals using our native eval system
            pass_rate, results = await run_tune_eval(
                evals,
                temp_skill_path,
                config.samples,
                config.parallel,
                callbacks.on_eval_status,
            )

            # Record this round
            round_result = RoundResult(
                round=round_num,
                pass_rate=pass_rate,
                skill_content=current_skill_content,
                tip_used="DSPy GroundedProposer",
                evals=results_to_eval_results(results),
            )
            tune_result.add_round(round_result)

            # Track for instruction proposal
            instruction_history.append(
                {
                    "instruction": current_skill_content,
                    "score": pass_rate / 100,  # Normalize to 0-1
                }
            )

            if callbacks.on_round_complete:
                await callbacks.on_round_complete(round_num, pass_rate, results)

            if pass_rate >= config.target_pass_rate:
                tune_result.finalize(success=True)
                # Save final skill and notify
                original_skill_file.write_text(tune_result.best_skill + "\n")
                if callbacks.on_complete:
                    await callbacks.on_complete(original_skill_file)
                return tune_result

            # Generate new instruction using DSPy's proposal mechanism
            if callbacks.on_improving:
                await callbacks.on_improving("Improving skill...")

            new_instruction = propose_instruction(
                current_instruction=current_skill_content,
                trainset=trainset,
                failures=[r for r in results if not r["pass"]],
                instruction_history=instruction_history,
            )

            current_skill_content = new_instruction
            temp_skill_path.write_text(new_instruction + "\n")

            # Save improved skill to original file (for interrupt safety)
            original_skill_file.write_text(new_instruction + "\n")

            if callbacks.on_improved:
                await callbacks.on_improved(new_instruction, original_skill_file)

        tune_result.finalize(success=False)
        # Save best skill and notify
        original_skill_file.write_text(tune_result.best_skill + "\n")
        if callbacks.on_complete:
            await callbacks.on_complete(original_skill_file)
        return tune_result
