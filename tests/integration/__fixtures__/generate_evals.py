"""Fixtures for generate_evals integration tests."""

from pathlib import Path

SAMPLE_SKILL = (Path(__file__).parent / "sample_skill.txt").read_text()

SAMPLE_GENERATED_EVALS = {
    "candidates": [
        {
            "prompt": "I tried to fetch https://api.example.com/data but WebFetch failed",
            "expected": "Suggests curl with appropriate flags",
            "name": "positive-goal1-browser-fail",
            "category": "positive",
            "source": "goal:1",
            "confidence": 0.85,
            "rationale": "Tests the primary goal of suggesting curl on browser failure",
        },
        {
            "prompt": "Please fetch this JavaScript-heavy SPA page",
            "expected": "Warns that curl won't execute JavaScript",
            "name": "positive-goal3-js-warning",
            "category": "positive",
            "source": "goal:3",
            "confidence": 0.75,
            "rationale": "Tests handling of JS-heavy pages per prohibition",
        },
        {
            "prompt": "The browser timed out, try again please",
            "expected": "Should NOT retry browser operation multiple times",
            "name": "negative-prohibition1-no-retry",
            "category": "negative",
            "source": "prohibition:1",
            "confidence": 0.9,
            "rationale": "Tests the prohibition against multiple retries",
        },
    ]
}
