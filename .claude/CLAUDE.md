Ensure all work happens in a git worktree. There should always be an issue on Github for work, that gets tied to a PR. After pushing a PR monitor it to make sure all CI checks go green. Before pushing, lint and run unit tests.

## Commit Convention

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/) format for automatic version bumping:

- `fix: ...` → patch release (0.1.0 → 0.1.1)
- `feat: ...` → minor release (0.1.0 → 0.2.0)
- `feat!: ...` or `BREAKING CHANGE:` in body → major release (0.1.0 → 1.0.0)
- `chore:`, `docs:`, `refactor:`, `test:`, etc. → patch release

PRs labeled with `skip-release` will not trigger version bumps or releases.
