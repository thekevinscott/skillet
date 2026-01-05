"""MIPROv2 wrapper with callback hooks for Skillet's UX."""

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any, cast

from dspy.teleprompt import MIPROv2
from dspy.teleprompt.mipro_optimizer_v2 import eval_candidate_program, save_candidate_program

from .dataclasses import TrialResult

logger = logging.getLogger(__name__)

# Type alias for sync callbacks (async not supported - DSPy optimization loop is sync)
CallbackType = Callable[..., None] | None


class SkilletMIPRO(MIPROv2):
    """MIPROv2 with callback hooks for progress reporting.

    Extends MIPROv2 to inject callbacks at key points:
    - on_trial_start: Called when a trial begins
    - on_trial_complete: Called when a trial finishes with its score
    - on_new_best: Called when a new best program is found

    Example:
        optimizer = SkilletMIPRO(
            metric=metric,
            on_trial_complete=lambda r: print(f"Trial {r.trial_num}: {r.score}")
        )
        optimized = optimizer.compile(module, trainset=data)
    """

    _on_trial_start: CallbackType
    _on_trial_complete: CallbackType
    _on_new_best: CallbackType
    _current_instruction_candidates: dict[int, list[str]]

    def __init__(
        self,
        metric: Callable,
        *,
        on_trial_start: CallbackType = None,
        on_trial_complete: CallbackType = None,
        on_new_best: CallbackType = None,
        **kwargs,
    ):
        """Initialize SkilletMIPRO with callbacks.

        Args:
            metric: DSPy metric function
            on_trial_start: Called at start of each trial (trial_num, total_trials)
            on_trial_complete: Called after each trial with TrialResult
            on_new_best: Called when a new best score is achieved
            **kwargs: Passed to MIPROv2
        """
        super().__init__(metric=metric, **kwargs)
        self._on_trial_start = on_trial_start
        self._on_trial_complete = on_trial_complete
        self._on_new_best = on_new_best
        self._current_instruction_candidates = {}

    def _optimize_prompt_parameters(  # noqa: C901, PLR0913, PLR0915
        self,
        program: Any,
        instruction_candidates: dict[int, list[str]],
        demo_candidates: list | None,
        evaluate: Any,
        valset: list,
        num_trials: int,
        minibatch: bool,
        minibatch_size: int,
        minibatch_full_eval_steps: int,
        seed: int,
    ) -> Any | None:
        """Override to inject callbacks into the optimization loop."""
        import optuna

        # Store for callback access
        self._current_instruction_candidates = instruction_candidates

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        logger.info("==> STEP 3: FINDING OPTIMAL PROMPT PARAMETERS <==")

        # Compute adjusted total trials
        run_additional = 1 if num_trials % minibatch_full_eval_steps != 0 else 0
        adjusted_num_trials = int(
            (num_trials + num_trials // minibatch_full_eval_steps + 1 + run_additional)
            if minibatch
            else num_trials
        )

        # Evaluate default program
        if self._on_trial_start:
            self._on_trial_start(1, adjusted_num_trials)

        default_score = eval_candidate_program(
            len(valset), valset, program, evaluate, self.rng
        ).score
        logger.info(f"Default program score: {default_score}")

        trial_logs = {}
        trial_logs[1] = {
            "full_eval_program_path": save_candidate_program(program, self.log_dir, -1),
            "full_eval_score": default_score,
            "total_eval_calls_so_far": len(valset),
            "full_eval_program": program.deepcopy(),
        }

        # Callback for default evaluation
        default_result = TrialResult(
            trial_num=1,
            score=default_score,
            is_best=True,
            instruction=self._get_current_instruction(program),
            is_full_eval=True,
        )
        if self._on_trial_complete:
            self._on_trial_complete(default_result)
        if self._on_new_best:
            self._on_new_best(default_result)

        # Initialize optimization state
        best_score = default_score
        best_program = program.deepcopy()
        total_eval_calls = len(valset)
        score_data = [{"score": best_score, "program": program.deepcopy(), "full_eval": True}]
        param_score_dict = defaultdict(list)
        fully_evaled_param_combos = {}

        def objective(trial):
            nonlocal program, best_program, best_score, trial_logs, total_eval_calls, score_data

            trial_num = trial.number + 2  # +2 because trial 1 is default
            if self._on_trial_start:
                self._on_trial_start(trial_num, adjusted_num_trials)

            trial_logs[trial_num] = {}
            candidate_program = program.deepcopy()

            # Select instructions and demos
            chosen_params, _ = self._select_and_insert_instructions_and_demos(
                candidate_program,
                instruction_candidates,
                demo_candidates,
                trial,
                trial_logs,
                trial_num,
            )

            # Evaluate
            batch_size = minibatch_size if minibatch else len(valset)
            score = eval_candidate_program(
                batch_size, valset, candidate_program, evaluate, self.rng
            ).score
            total_eval_calls += batch_size

            is_new_best = False
            if not minibatch and score > best_score:
                best_score = score
                best_program = candidate_program.deepcopy()
                is_new_best = True
                logger.info(f"New best score: {score}")

            score_data.append(
                {
                    "score": score,
                    "program": candidate_program,
                    "full_eval": batch_size >= len(valset),
                }
            )

            # Callbacks
            result = TrialResult(
                trial_num=trial_num,
                score=score,
                is_best=is_new_best,
                instruction=self._get_current_instruction(candidate_program),
                is_full_eval=batch_size >= len(valset),
            )
            if self._on_trial_complete:
                self._on_trial_complete(result)
            if is_new_best and self._on_new_best:
                self._on_new_best(result)

            # Track for minibatch full eval
            if minibatch:
                param_score_dict[chosen_params].append(score)
                self._log_minibatch_eval(
                    score,
                    best_score,
                    batch_size,
                    chosen_params,
                    score_data,
                    trial,
                    adjusted_num_trials,
                    trial_logs,
                    trial_num,
                    candidate_program,
                    total_eval_calls,
                )
            else:
                self._log_normal_eval(
                    score,
                    best_score,
                    chosen_params,
                    score_data,
                    trial,
                    num_trials,
                    trial_logs,
                    trial_num,
                    valset,
                    batch_size,
                    candidate_program,
                    total_eval_calls,
                )

            # Minibatch full evaluation at intervals
            if minibatch and (trial.number + 1) % minibatch_full_eval_steps == 0:
                (
                    best_score,
                    best_program,
                    total_eval_calls,
                ) = self._perform_full_evaluation(
                    trial_num,
                    adjusted_num_trials,
                    param_score_dict,
                    fully_evaled_param_combos,
                    evaluate,
                    valset,
                    trial_logs,
                    total_eval_calls,
                    score_data,
                    best_score,
                    best_program,
                    study,
                    cast(list, instruction_candidates),
                    cast(list, demo_candidates or []),
                )

            return score

        # Create and run Optuna study
        sampler = optuna.samplers.TPESampler(seed=seed, multivariate=True)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(objective, n_trials=num_trials, show_progress_bar=False)

        # Final full evaluation if needed
        if minibatch and num_trials % minibatch_full_eval_steps != 0:
            (
                best_score,
                best_program,
                total_eval_calls,
            ) = self._perform_full_evaluation(
                num_trials + 1,
                adjusted_num_trials,
                param_score_dict,
                fully_evaled_param_combos,
                evaluate,
                valset,
                trial_logs,
                total_eval_calls,
                score_data,
                best_score,
                best_program,
                study,
                cast(list, instruction_candidates),
                cast(list, demo_candidates or []),
            )

        best_program.trial_logs = trial_logs
        return best_program

    def _get_current_instruction(self, program: Any) -> str:
        """Extract current instruction from program."""
        try:
            # For SkillModule, get the signature instructions
            if hasattr(program, "predictor") and hasattr(program.predictor, "signature"):
                return program.predictor.signature.instructions or ""
            # Fallback: try to get from first predictor
            for _name, module in program.named_predictors():
                if hasattr(module, "signature"):
                    return module.signature.instructions or ""
        except Exception:  # nosec B110 - intentional catch-all for varied DSPy structures
            pass
        return ""
