# Shipping

How Skillet cuts releases. Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (see [`repo.md`](repo.md#commit-convention)).

## Releases

Patch releases are controlled by the `RELEASE_STRATEGY` repo variable (Settings > Secrets and variables > Actions > Variables):

- **`nightly`** (default when unset) — patch releases run on a daily cron at 2am UTC
- **`immediate`** — patch releases cut on every push to main

Other release types:
- **Minor releases** are triggered manually via GitHub Actions > "Minor Release"
- **Major releases** are done manually by creating a tag
- **`workflow_dispatch`** always works regardless of strategy (manual override)

To skip a release in immediate mode, include `[no-release]` in the commit message.
