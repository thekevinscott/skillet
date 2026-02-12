#!/usr/bin/env python3
"""Analyze SKILL.md files for anatomy components."""

import re
import sqlite3
from dataclasses import dataclass


@dataclass
class SkillScore:
    url: str
    score: int
    word_count: int
    components_present: list[str]
    components_missing: list[str]
    raw_text: str


def score_skill(url: str, raw_text: str) -> SkillScore | None:
    """Score a skill against 9 anatomy components."""
    # Count words
    word_count = len(raw_text.split())
    if word_count < 100:
        return None

    text_lower = raw_text.lower()

    components = {
        "Trigger": bool(re.search(r"(when to use|use this when|## when|## trigger)", text_lower)),
        "Persona": bool(re.search(r"you are (a|an|the)", text_lower)),
        "What to do": True,  # Always present (imperative instructions)
        "What not to do": bool(
            re.search(r"(never |do not |don.t |avoid |anti.?pattern)", text_lower)
        ),
        "Why": bool(
            re.search(
                r"(## why|## rationale|## purpose|because |this ensures|## principle)",
                text_lower,
            )
        ),
        "Examples": raw_text.count("```") >= 2,  # At least one complete code block
        "Output format": bool(
            re.search(
                r"(## output|output format|## report|output schema|response format|## format)",
                text_lower,
            )
        ),
        "Verification": bool(
            re.search(
                r"(## verif|## valid|## check|confirm that|verify that|## quality|## success)",
                text_lower,
            )
        ),
        "References": bool(
            re.search(
                r"(## see also|## refer|## resource|docs/|\.md\b|related skill|## additional)",
                text_lower,
            )
        ),
    }

    score = sum(components.values())
    present = [name for name, has in components.items() if has]
    missing = [name for name, has in components.items() if not has]

    return SkillScore(
        url=url,
        score=score,
        word_count=word_count,
        components_present=present,
        components_missing=missing,
        raw_text=raw_text,
    )


def main():
    # Connect to database
    conn = sqlite3.connect("data/analyzed/content.db")
    cursor = conn.cursor()

    # Read 50 skills
    cursor.execute("SELECT url, raw FROM content ORDER BY url LIMIT 50 OFFSET 50")
    rows = cursor.fetchall()

    # Score each skill
    scored_skills = []
    for url, raw_bytes in rows:
        try:
            # Decode directly - data is not compressed
            raw_text = raw_bytes.decode("utf-8", errors="replace")
            result = score_skill(url, raw_text)
            if result:
                scored_skills.append(result)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue

    # Sort by score descending
    scored_skills.sort(key=lambda x: x.score, reverse=True)

    # Print top 5
    print("=" * 80)
    print("TOP 5 SKILLS BY ANATOMY COMPONENT SCORE")
    print("=" * 80)
    print()

    for i, skill in enumerate(scored_skills[:5], 1):
        print(f"{i}. SCORE: {skill.score}/9 | Words: {skill.word_count}")
        print(f"   URL: {skill.url}")
        print(f"   Present: {', '.join(skill.components_present)}")
        print(f"   Missing: {', '.join(skill.components_missing)}")
        print()

    # Print full text of highest-scoring skill
    if scored_skills:
        best = scored_skills[0]
        print("=" * 80)
        print(f"FULL TEXT OF HIGHEST-SCORING SKILL ({best.score}/9)")
        print(f"URL: {best.url}")
        print("=" * 80)
        print()
        print(best.raw_text)

    conn.close()


if __name__ == "__main__":
    main()
