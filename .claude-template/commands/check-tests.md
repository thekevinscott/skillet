# Check Test Consistency

Verify that e2e tests and integration tests cover the same behavior and expect the same outcomes.

## Rules

1. **Mirror coverage**: Every e2e test in `tests/e2e/cli/` should have a corresponding integration test in `tests/integration/` that covers the same scenario, and vice versa.

2. **Same expectations**: If an e2e test expects a command to exit 0, the integration test must expect the underlying Python function to succeed (not raise). If an e2e test expects a nonzero exit, the integration test must expect an exception.

3. **Same test names**: Use consistent naming between e2e and integration tests for the same scenario (e.g., `it_errors_when_no_eval_files_exist` in both).

4. **Same fixture data**: Both test layers should use the same fixture content and setup patterns. An integration test should not test with data that the e2e test never exercises.

5. **`no_mirror` exemption**: Tests decorated with `@pytest.mark.no_mirror` are intentionally layer-specific (e.g., integration tests mocking non-deterministic API responses that have no meaningful e2e equivalent). These tests are exempt from mirror coverage requirements.

## Procedure

1. List all test files in `tests/e2e/cli/` and `tests/integration/`.
2. For each e2e test file, find the corresponding integration test file.
3. Compare the test function names and their assertions.
4. Before flagging a test as `MISSING`, check whether it is decorated with `@pytest.mark.no_mirror`. If it is, report it as `SKIPPED` instead.
5. Flag any scenario where the two layers expect different outcomes.

## Output

Report discrepancies as a list:
- `MISSING`: test exists in one layer but not the other (and is NOT marked `no_mirror`)
- `SKIPPED`: test exists in one layer only but is marked `@pytest.mark.no_mirror` — no counterpart required
- `MISMATCH`: test exists in both but expects different outcomes
- `OK`: test exists in both and expects the same outcome

If discrepancies are found, suggest specific fixes.
