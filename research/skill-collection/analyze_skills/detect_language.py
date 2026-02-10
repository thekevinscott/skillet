"""Add language detection column to content_features.parquet.

Reads the features parquet, detects language from prose content (stripping
frontmatter and code blocks), and writes the result back with a `language`
column added.

This is slow (~20-30 min for 385k files) so it's separated from the fast
extract_features pipeline.

Usage:
    python -m analyze_skills.detect_language [--input PATH] [--output PATH]

Defaults:
    --input   data/analyzed/content_features.parquet
    --output  data/analyzed/content_features.parquet  (overwrites in place)
"""

import argparse
import re
import sys
from pathlib import Path

import polars as pl
from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0  # deterministic detection

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_DEFAULT = _DATA_DIR / "analyzed" / "content_features.parquet"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")


def detect_language(text: str) -> str:
    """Detect language from prose content."""
    # Strip frontmatter
    normalized = FRONTMATTER_RE.sub("", text.lstrip(), count=1)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    # Strip code blocks
    prose = CODE_BLOCK_RE.sub("", normalized)
    try:
        return detect(prose) if len(prose.split()) >= 10 else "unknown"
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_DEFAULT,
        help=f"Input features parquet (default: {INPUT_DEFAULT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output parquet path (default: same as input)",
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=_DATA_DIR / "content",
        help="Directory containing content files",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path = args.output or input_path
    content_dir: Path = args.content_dir.expanduser().resolve()

    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pl.read_parquet(input_path)

    if "language" in df.columns:
        already = df.filter(pl.col("language") != "").shape[0]
        print(f"Already has language column ({already:,} non-empty). Skipping.")
        return

    total = df.shape[0]
    print(f"Detecting language for {total:,} files...")

    languages = []
    for i, url in enumerate(df["url"].to_list()):
        if i % 10_000 == 0:
            print(f"  {i:,}/{total:,} ({100 * i / total:.0f}%)...", flush=True)
        rel = url.replace("https://github.com/", "")
        path = content_dir / rel
        if path.exists():
            try:
                text = path.read_text(errors="replace")
            except OSError:
                text = ""
        else:
            text = ""
        languages.append(detect_language(text))

    df = df.with_columns(pl.Series("language", languages))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path)
    print(f"Wrote {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
