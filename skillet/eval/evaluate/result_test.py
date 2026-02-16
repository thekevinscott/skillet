"""Tests for evaluate result dataclasses."""

from skillet.eval.evaluate.result import EvaluateResult, IterationResult, PerEvalMetric


def describe_iteration_result():
    def it_constructs_with_required_fields():
        r = IterationResult(
            eval_idx=0,
            eval_source="001.yaml",
            iteration=1,
            response="hello",
            passed=True,
        )
        assert r.eval_idx == 0
        assert r.passed is True
        assert r.cached is False
        assert r.tool_calls is None

    def it_maps_passed_to_pass_in_to_dict():
        r = IterationResult(
            eval_idx=0,
            eval_source="001.yaml",
            iteration=1,
            response="hello",
            passed=True,
        )
        d = r.to_dict()
        assert "pass" in d
        assert "passed" not in d
        assert d["pass"] is True

    def it_roundtrips_all_fields():
        r = IterationResult(
            eval_idx=1,
            eval_source="002.yaml",
            iteration=2,
            response="world",
            passed=False,
            tool_calls=[{"name": "Bash"}],
            judgment={"pass": False, "reasoning": "wrong"},
            cached=True,
        )
        d = r.to_dict()
        assert d["eval_idx"] == 1
        assert d["eval_source"] == "002.yaml"
        assert d["iteration"] == 2
        assert d["response"] == "world"
        assert d["pass"] is False
        assert d["tool_calls"] == [{"name": "Bash"}]
        assert d["judgment"]["reasoning"] == "wrong"
        assert d["cached"] is True


def describe_per_eval_metric():
    def it_constructs_with_all_fields():
        m = PerEvalMetric(
            eval_source="001.yaml",
            pass_at_k=0.95,
            pass_pow_k=0.80,
            k=3,
            n=3,
            c=2,
        )
        assert m.eval_source == "001.yaml"
        assert m.pass_at_k == 0.95


def describe_evaluate_result():
    def it_constructs_and_serializes():
        iteration = IterationResult(
            eval_idx=0,
            eval_source="001.yaml",
            iteration=1,
            response="hi",
            passed=True,
        )
        metric = PerEvalMetric(
            eval_source="001.yaml",
            pass_at_k=1.0,
            pass_pow_k=1.0,
            k=1,
            n=1,
            c=1,
        )
        result = EvaluateResult(
            results=[iteration],
            tasks=[{"eval_idx": 0}],
            pass_rate=100.0,
            total_runs=1,
            total_pass=1,
            cached_count=0,
            fresh_count=1,
            total_evals=1,
            sampled_evals=1,
            per_eval_metrics=[metric],
        )
        d = result.to_dict()
        assert d["pass_rate"] == 100.0
        assert len(d["results"]) == 1
        assert d["results"][0]["pass"] is True
        assert d["per_eval_metrics"][0]["pass_at_k"] == 1.0
