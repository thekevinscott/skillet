"""Generic DSPy prompt optimizer: takes labeled examples JSON, produces an optimized prompt.

Uses Claude Agent SDK (via claude_agent_sdk) for LLM calls — no API key needed.

Usage:
    uv run --with 'dspy>=2.6' python tools/optimize_prompt.py \
        --input /tmp/skill-labels.json \
        --output /tmp/anatomy-prompt.txt
"""

import argparse
import asyncio
import json
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import dspy
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query
from dspy.clients.base_lm import BaseLM

# ---------------------------------------------------------------------------
# Minimal Claude Agent SDK LM for DSPy (self-contained, no skillet dependency)
# ---------------------------------------------------------------------------


@dataclass
class _Message:
    role: str
    content: str


@dataclass
class _Choice:
    index: int
    message: _Message


@dataclass
class _CompletionResponse:
    id: str
    model: str
    choices: list[_Choice]
    usage: dict = field(default_factory=dict)


def _extract_prompt(prompt: str | None, messages: list[dict] | None) -> str:
    """Convert DSPy's prompt/messages into a single string for Claude."""
    if prompt:
        return prompt
    if messages:
        parts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
            parts.append(content)
        return "\n\n".join(parts)
    return ""


async def _query_text(prompt: str) -> str:
    """Query Claude Agent SDK and return the assistant's text response."""
    opts = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    result = ""
    async for message in query(prompt=prompt, options=opts):
        if isinstance(message, AssistantMessage) and hasattr(message, "content"):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result += block.text
    return result.strip()


def _run_sync(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class ClaudeAgentLM(BaseLM):
    """DSPy LM that wraps Claude Agent SDK. No API key needed."""

    def __init__(self, model: str = "claude-agent-sdk", model_type: str = "chat", **kwargs):
        self.model = model
        self.model_type = model_type
        self.kwargs = kwargs
        self.history: list[dict] = []

    def forward(self, prompt=None, messages=None, **kwargs) -> _CompletionResponse:
        text = _extract_prompt(prompt, messages)
        response = _run_sync(_query_text(text))
        result = _CompletionResponse(
            id=f"claude-{uuid.uuid4().hex[:8]}",
            model=self.model,
            choices=[_Choice(index=0, message=_Message(role="assistant", content=response))],
        )
        self.history.append({"prompt": text, "response": result, "kwargs": kwargs})
        return result

    async def aforward(self, prompt=None, messages=None, **kwargs) -> _CompletionResponse:
        text = _extract_prompt(prompt, messages)
        response = await _query_text(text)
        result = _CompletionResponse(
            id=f"claude-{uuid.uuid4().hex[:8]}",
            model=self.model,
            choices=[_Choice(index=0, message=_Message(role="assistant", content=response))],
        )
        self.history.append({"prompt": text, "response": result, "kwargs": kwargs})
        return result

    def copy(self, **kwargs):
        new_kwargs = {**self.kwargs, **kwargs}
        return ClaudeAgentLM(model=self.model, model_type=self.model_type, **new_kwargs)

    def update_history(self, entry):
        self.history.append(entry)

    def inspect_history(self, n=1):
        return self.history[-n:]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def load_examples(path: str, input_field: str, output_field: str):
    """Load examples from JSON file."""
    data = json.loads(Path(path).read_text())
    examples = []
    for ex in data["examples"]:
        example = dspy.Example(**{input_field: ex[input_field], output_field: ex[output_field]})
        examples.append(example.with_inputs(input_field))
    return examples, data.get("task", ""), data.get("labels", [])


def stratified_split(examples, output_field: str, train_ratio: float, seed: int = 42):
    """Split examples into train/val sets, stratified by output field."""
    rng = random.Random(seed)
    by_label = defaultdict(list)
    for ex in examples:
        by_label[getattr(ex, output_field)].append(ex)

    train, val = [], []
    for _label, items in by_label.items():
        rng.shuffle(items)
        split = max(1, int(len(items) * train_ratio))
        train.extend(items[:split])
        val.extend(items[split:])

    # If val is empty (all labels had only 1 example), move some from train
    if not val:
        rng.shuffle(train)
        split = max(1, int(len(train) * train_ratio))
        val = train[split:]
        train = train[:split]

    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def make_metric(output_field: str):
    """Create an exact-match metric for the output field."""

    def metric(example, prediction, trace=None):
        expected = getattr(example, output_field, "").strip().lower()
        predicted = getattr(prediction, output_field, "").strip().lower()
        return expected == predicted

    return metric


def extract_prompt(program, input_field: str, output_field: str, labels: list[str]) -> str:
    """Extract the optimized prompt from a compiled DSPy program."""
    parts = []

    sig = getattr(program, "extended_signature", program.signature)
    instructions = sig.instructions
    if instructions:
        parts.append(instructions.strip())

    demos = getattr(program, "demos", [])
    if demos:
        parts.append("\nExamples:")
        for demo in demos:
            inp = getattr(demo, input_field, "")
            out = getattr(demo, output_field, "")
            parts.append(f"---\nInput: {inp}\nOutput: {out}")
        parts.append("---")

    if labels:
        parts.append(f"\nAvailable labels: {', '.join(labels)}")

    parts.append(f"\nInput: {{{input_field}}}\nOutput:")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Optimize a classification prompt with DSPy MIPROv2"
    )
    parser.add_argument("--input", required=True, help="JSON file with labeled examples")
    parser.add_argument("--output", required=True, help="Output path for the optimized prompt")
    parser.add_argument("--input-field", default="text", help="Input field name (default: text)")
    parser.add_argument("--output-field", default="tag", help="Output field name (default: tag)")
    parser.add_argument("--num-candidates", type=int, default=5, help="Instruction candidates")
    parser.add_argument("--num-trials", type=int, default=15, help="Optuna trials for MIPROv2")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train/val split ratio")
    args = parser.parse_args()

    # Load data
    print(f"Loading examples from {args.input}...")
    examples, task, labels = load_examples(args.input, args.input_field, args.output_field)
    print(f"  {len(examples)} examples, {len(labels)} labels")

    # Split
    train, val = stratified_split(examples, args.output_field, args.train_ratio)
    print(f"  Train: {len(train)}, Val: {len(val)}")

    # Build signature
    label_list = ", ".join(labels) if labels else "see examples"
    task_desc = task or "Classify the input"
    instructions = f"{task_desc}. Choose exactly one label from: {label_list}"

    signature = dspy.Signature(
        f"{args.input_field} -> {args.output_field}",
        instructions=instructions,
    )

    # Configure LM via Claude Agent SDK
    lm = ClaudeAgentLM()
    dspy.configure(lm=lm)

    # Define program
    program = dspy.Predict(signature)

    # Define metric
    metric = make_metric(args.output_field)

    # Run MIPROv2
    print(f"\nRunning MIPROv2 ({args.num_candidates} candidates, {args.num_trials} trials)...")
    optimizer = dspy.MIPROv2(
        metric=metric,
        auto=None,
        num_candidates=args.num_candidates,
        num_threads=1,
    )
    optimized = optimizer.compile(
        program,
        trainset=train,
        valset=val,
        num_trials=args.num_trials,
        minibatch=False,
        requires_permission_to_run=False,
    )

    # Evaluate on val set
    correct = sum(
        1
        for ex in val
        if metric(ex, optimized(**{args.input_field: getattr(ex, args.input_field)}))
    )
    print(f"\nVal accuracy: {correct}/{len(val)} ({correct / len(val) * 100:.1f}%)")

    # Extract and write prompt
    prompt = extract_prompt(optimized, args.input_field, args.output_field, labels)
    Path(args.output).write_text(prompt)
    print(f"\nOptimized prompt written to {args.output}")
    print("=" * 60)
    print(prompt)
    print("=" * 60)


if __name__ == "__main__":
    main()
