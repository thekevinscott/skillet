"""Scan skill content files and extract structural features to parquet.

Reads all .md files from a content directory and computes per-file metrics:
byte size, word/line/paragraph counts, markdown structure, frontmatter fields.

Usage:
    python -m analyze_skills.extract_features [--content-dir PATH] [--output PATH]

Defaults:
    --content-dir ~/work/skills-dataset/data/content/
    --output      data/content_features.parquet
"""

import argparse
import re
import sys
from pathlib import Path

import polars as pl

CONTENT_DIR_DEFAULT = Path.home() / "work" / "skills-dataset" / "data" / "content"
OUTPUT_DEFAULT = Path(__file__).resolve().parent.parent / "data" / "content_features.parquet"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s", re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"^```", re.MULTILINE)
URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
YAML_KEY_RE = re.compile(r"^(\w[\w_-]*):", re.MULTILINE)


def extract_features(path: Path, content_dir: Path) -> dict:
    """Extract structural features from a single skill file."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    byte_size = len(raw)
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    # Reconstruct URL from path
    rel = path.relative_to(content_dir)
    url = "https://github.com/" + str(rel)

    # Basic counts
    words = len(text.split())
    lines = text.count("\n") + 1 if text else 0
    # Paragraphs: blank-line-delimited blocks (consecutive non-empty lines)
    paragraphs = len([b for b in re.split(r"\n\s*\n", text) if b.strip()])

    # Heading analysis
    headings = HEADING_RE.findall(text)
    heading_count = len(headings)
    max_heading_depth = max((len(h) for h in headings), default=0)

    # Code blocks (``` pairs)
    code_fences = len(CODE_BLOCK_RE.findall(text))
    code_block_count = code_fences // 2

    # URL count
    url_count = len(URL_RE.findall(text))

    # Frontmatter
    has_frontmatter = text.lstrip().startswith("---")
    frontmatter_fields: list[str] = []
    if has_frontmatter:
        fm_match = FRONTMATTER_RE.match(text.lstrip())
        if fm_match:
            fm_text = fm_match.group(1)
            frontmatter_fields = YAML_KEY_RE.findall(fm_text)

    return {
        "url": url,
        "bytes": byte_size,
        "words": words,
        "lines": lines,
        "paragraphs": paragraphs,
        "heading_count": heading_count,
        "max_heading_depth": max_heading_depth,
        "code_block_count": code_block_count,
        "url_count": url_count,
        "has_frontmatter": has_frontmatter,
        "frontmatter_fields": frontmatter_fields,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=CONTENT_DIR_DEFAULT,
        help=f"Directory containing content files (default: {CONTENT_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
        help=f"Output parquet path (default: {OUTPUT_DEFAULT})",
    )
    args = parser.parse_args()

    content_dir: Path = args.content_dir.expanduser().resolve()
    output: Path = args.output

    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect all .md files
    print(f"Scanning {content_dir} for .md files...")
    all_files = sorted(content_dir.rglob("*.md"))
    total = len(all_files)
    print(f"Found {total:,} files")

    # Extract features with progress reporting
    rows: list[dict] = []
    for i, path in enumerate(all_files):
        if i % 10_000 == 0:
            print(f"  Processing {i:,}/{total:,} ({100 * i / total:.0f}%)...", flush=True)
        result = extract_features(path, content_dir)
        if result is not None:
            rows.append(result)

    print(f"Extracted features from {len(rows):,} files")

    # Build dataframe and write
    df = pl.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output)
    print(f"Wrote {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Schema: {df.schema}")


if __name__ == "__main__":
    main()
