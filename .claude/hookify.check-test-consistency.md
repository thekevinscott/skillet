---
name: check-test-consistency
enabled: true
event: bash
pattern: git commit
action: block
---

**Test consistency check required**

Before committing, verify that e2e and integration tests are consistent:
- Run `/check-tests` to audit test coverage across both layers
- Every e2e test should have a corresponding integration test and vice versa
- Both layers must expect the same outcomes for the same scenarios
