"""Fixtures for generate_evals integration tests."""

SAMPLE_SKILL = (
    "---\n"
    "name: browser-fallback\n"
    "description: Suggests curl when browser tools fail\n"
    "---\n"
    "\n"
    "# Browser Fallback Skill\n"
    "\n"
    "## Goals\n"
    "\n"
    "1. When a browser tool fails, suggest using curl instead\n"
    "2. Provide actionable curl command examples\n"
    "3. Handle authentication scenarios gracefully\n"
    "\n"
    "## Prohibitions\n"
    "\n"
    "- Never retry failed browser operations more than once\n"
    "- Don't suggest curl for JavaScript-heavy pages without warning\n"
)

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
