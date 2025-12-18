# Improve a Skill

You are improving a SKILL.md file based on eval failures. Your goal is to revise the skill so Claude exhibits the expected behavior.

## Input Format

You will receive:
1. **Current SKILL.md** — The skill content to improve
2. **Passing Tests** — Tests that currently work (DO NOT BREAK THESE)
3. **Failures** — Tests that failed with prompt, expected behavior, and actual response
4. **Constraints** — Line limits and style tips

## Your Task

Revise the SKILL.md to fix failures while PRESERVING behavior for passing tests.

**CRITICAL: Do not break what's working!** The passing tests represent behavior that must continue to work after your changes.

## Common Issues to Fix

- Description not specific enough about WHEN to trigger
- Instructions not explicit enough (Claude defaults to asking permission)
- Missing "do NOT ask" or "IMMEDIATELY" language for automatic behaviors
- Trigger conditions too broad or too narrow

## Constraints

- Keep the SKILL.md under the specified line limit
- Be concise but complete — don't remove instructions that make passing tests work
- Add specific handling for failing cases without breaking passing ones
- Preserve frontmatter (the `---` section) if present

## Output Format

Return ONLY the improved SKILL.md content:
- No explanation
- No code fences
- No preamble
- Just the raw markdown content that should be written to the file
