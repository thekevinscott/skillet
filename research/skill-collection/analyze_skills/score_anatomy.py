#!/usr/bin/env python3
"""Score SKILL.md files by anatomy components."""

import argparse
import re
import sqlite3
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SkillScore:
    url: str
    score: int
    word_count: int
    present: list[str]
    missing: list[str]
    raw_text: str


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def score_skill(url: str, raw_text: str) -> SkillScore:
    """Score a skill against 9 anatomy components."""
    text_lower = raw_text.lower()

    components = {
        "Trigger": bool(
            re.search(r"when to use", text_lower)
            or re.search(r"use this when", text_lower)
            or re.search(r"## when", text_lower)
            or re.search(r"## trigger", text_lower)
            or re.search(r"activation condition", text_lower)
        ),
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
        "Examples": raw_text.count("```") >= 2,
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
    present = [name for name, has_it in components.items() if has_it]
    missing = [name for name, has_it in components.items() if not has_it]

    return SkillScore(
        url=url,
        score=score,
        word_count=count_words(raw_text),
        present=present,
        missing=missing,
        raw_text=raw_text,
    )


def main():
    parser = argparse.ArgumentParser(description="Score SKILL.md files by anatomy components")
    parser.add_argument("--offset", type=int, default=0, help="Offset for SQL query (default: 0)")
    args = parser.parse_args()

    db_path = Path("data/analyzed/content.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch 50 skills starting at the specified offset
    cursor.execute(f"SELECT url, raw FROM content ORDER BY url LIMIT 50 OFFSET {args.offset}")
    rows = cursor.fetchall()

    scores = []
    for url, raw_data in rows:
        # Decompress if compressed, otherwise decode directly
        try:
            raw_text = zlib.decompress(raw_data).decode("utf-8", errors="replace")
        except zlib.error:
            # Not compressed, decode directly
            raw_text = raw_data.decode("utf-8", errors="replace")

        # Skip if fewer than 100 words
        if count_words(raw_text) < 100:
            continue

        # Score the skill
        skill_score = score_skill(url, raw_text)
        scores.append(skill_score)

    # Sort by score descending
    scores.sort(key=lambda s: s.score, reverse=True)

    # Print top 5
    print("=" * 80)
    print(f"TOP 5 SKILLS BY ANATOMY SCORE (OFFSET {args.offset}-{args.offset + 49})")
    print("=" * 80)
    for i, skill in enumerate(scores[:5], 1):
        print(f"\n{i}. Score: {skill.score}/9 | Words: {skill.word_count} | {skill.url}")
        print(f"   Present: {', '.join(skill.present)}")
        print(f"   Missing: {', '.join(skill.missing)}")

    # Print full content of highest-scoring skill
    if scores:
        top_skill = scores[0]
        print("\n" + "=" * 80)
        print(f"FULL CONTENT OF HIGHEST-SCORING SKILL ({top_skill.score}/9)")
        print(f"URL: {top_skill.url}")
        print("=" * 80)
        print(top_skill.raw_text)

    conn.close()


if __name__ == "__main__":
    main()
