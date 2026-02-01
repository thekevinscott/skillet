"""Extract features from SKILL.md files for analysis."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
import polars as pl

from .github import parse_github_url


@dataclass
class SkillFeatures:
    """Extracted features from a single SKILL.md file."""

    # Identity
    url: str
    owner: str
    repo: str
    path: str

    # Basic stats
    byte_size: int
    line_count: int
    word_count: int

    # Frontmatter
    has_frontmatter: bool
    frontmatter_bytes: int
    frontmatter_fields: list[str] = field(default_factory=list)

    # Standard frontmatter fields
    has_name: bool = False
    has_description: bool = False
    has_license: bool = False
    has_metadata: bool = False
    has_triggers: bool = False
    has_model: bool = False
    has_allowed_tools: bool = False
    has_user_invocable: bool = False

    # Content structure
    has_h1: bool = False
    heading_count: int = 0
    code_block_count: int = 0
    code_languages: list[str] = field(default_factory=list)
    list_item_count: int = 0
    table_count: int = 0
    link_count: int = 0
    external_url_count: int = 0

    # Content patterns
    has_examples: bool = False
    has_when_to_use: bool = False
    has_references: bool = False

    def to_dict(self) -> dict:
        """Convert to dict for DataFrame creation."""
        return {
            "url": self.url,
            "owner": self.owner,
            "repo": self.repo,
            "path": self.path,
            "byte_size": self.byte_size,
            "line_count": self.line_count,
            "word_count": self.word_count,
            "has_frontmatter": self.has_frontmatter,
            "frontmatter_bytes": self.frontmatter_bytes,
            "frontmatter_field_count": len(self.frontmatter_fields),
            "has_name": self.has_name,
            "has_description": self.has_description,
            "has_license": self.has_license,
            "has_metadata": self.has_metadata,
            "has_triggers": self.has_triggers,
            "has_model": self.has_model,
            "has_allowed_tools": self.has_allowed_tools,
            "has_user_invocable": self.has_user_invocable,
            "has_h1": self.has_h1,
            "heading_count": self.heading_count,
            "code_block_count": self.code_block_count,
            "code_language_count": len(self.code_languages),
            "list_item_count": self.list_item_count,
            "table_count": self.table_count,
            "link_count": self.link_count,
            "external_url_count": self.external_url_count,
            "has_examples": self.has_examples,
            "has_when_to_use": self.has_when_to_use,
            "has_references": self.has_references,
        }


def parse_valid_md(valid_md_path: Path) -> list[str]:
    """Parse valid.md to extract skill URLs."""
    urls = []
    content = valid_md_path.read_text()

    # Extract URLs from markdown table links: <a href="URL" ...>
    pattern = r'<a href="([^"]+)"'
    for match in re.finditer(pattern, content):
        urls.append(match.group(1))

    return urls


def extract_features(url: str, content: str, parsed: tuple) -> SkillFeatures:
    """Extract features from a skill file's content."""
    owner, repo, ref, path = parsed

    # Basic stats
    byte_size = len(content.encode("utf-8"))
    lines = content.split("\n")
    line_count = len(lines)
    word_count = len(content.split())

    # Parse frontmatter
    try:
        post = frontmatter.loads(content)
        has_frontmatter = bool(post.metadata)
        frontmatter_fields = list(post.metadata.keys()) if post.metadata else []

        # Calculate frontmatter size (approximate)
        if has_frontmatter:
            # Find the closing --- of frontmatter
            fm_match = re.match(r"^---\n.*?\n---\n", content, re.DOTALL)
            frontmatter_bytes = len(fm_match.group(0).encode("utf-8")) if fm_match else 0
        else:
            frontmatter_bytes = 0

        body = post.content
        metadata = post.metadata or {}
    except Exception:
        has_frontmatter = False
        frontmatter_fields = []
        frontmatter_bytes = 0
        body = content
        metadata = {}

    # Check standard frontmatter fields
    has_name = "name" in metadata
    has_description = "description" in metadata
    has_license = "license" in metadata
    has_metadata = "metadata" in metadata
    has_model = "model" in metadata
    has_allowed_tools = "allowed-tools" in metadata or "allowed_tools" in metadata
    has_user_invocable = "user-invocable" in metadata or "user_invocable" in metadata

    # Check for triggers (can be in metadata or at top level)
    has_triggers = "triggers" in metadata
    if has_metadata and isinstance(metadata.get("metadata"), dict):
        has_triggers = has_triggers or "triggers" in metadata["metadata"]

    # Content structure analysis
    has_h1 = bool(re.search(r"^# ", body, re.MULTILINE))
    heading_count = len(re.findall(r"^#{1,6} ", body, re.MULTILINE))

    # Code blocks
    code_blocks = re.findall(r"```(\w*)", body)
    code_block_count = len(code_blocks)
    code_languages = [lang for lang in code_blocks if lang]

    # Lists
    list_item_count = len(re.findall(r"^[\s]*[-*+]\s", body, re.MULTILINE))
    list_item_count += len(re.findall(r"^[\s]*\d+\.\s", body, re.MULTILINE))

    # Tables
    table_count = len(re.findall(r"^\|.*\|.*\|", body, re.MULTILINE))

    # Links
    links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", body)
    link_count = len(links)
    external_url_count = sum(1 for _, url in links if url.startswith("http"))

    # Content patterns
    has_examples = bool(
        re.search(r"(?i)(example|usage|sample)", body)
        or re.search(r"```", body)
    )
    has_when_to_use = bool(
        re.search(r"(?i)(when to (use|activate)|trigger|invoke)", body)
    )
    has_references = bool(
        re.search(r"(?i)(reference|see also|documentation|docs)", body)
        or external_url_count > 0
    )

    return SkillFeatures(
        url=url,
        owner=owner,
        repo=repo,
        path=path,
        byte_size=byte_size,
        line_count=line_count,
        word_count=word_count,
        has_frontmatter=has_frontmatter,
        frontmatter_bytes=frontmatter_bytes,
        frontmatter_fields=frontmatter_fields,
        has_name=has_name,
        has_description=has_description,
        has_license=has_license,
        has_metadata=has_metadata,
        has_triggers=has_triggers,
        has_model=has_model,
        has_allowed_tools=has_allowed_tools,
        has_user_invocable=has_user_invocable,
        has_h1=has_h1,
        heading_count=heading_count,
        code_block_count=code_block_count,
        code_languages=code_languages,
        list_item_count=list_item_count,
        table_count=table_count,
        link_count=link_count,
        external_url_count=external_url_count,
        has_examples=has_examples,
        has_when_to_use=has_when_to_use,
        has_references=has_references,
    )


def cmd_analyze(args):
    """Extract features from valid skills and save to parquet."""
    valid_md_path = args.output_dir / "classified-skills" / "valid.md"
    content_dir = args.output_dir / "content"

    if not valid_md_path.exists():
        raise FileNotFoundError(f"{valid_md_path} not found. Run 'filter-skills' first.")

    # Parse valid.md to get URLs
    urls = parse_valid_md(valid_md_path)
    print(f"Found {len(urls)} valid skill URLs")

    # Extract features for each skill
    features_list = []
    errors = 0

    for i, url in enumerate(urls):
        parsed = parse_github_url(url)
        if not parsed:
            errors += 1
            continue

        owner, repo, ref, path = parsed
        local_path = content_dir / owner / repo / "blob" / ref / path

        if not local_path.exists():
            errors += 1
            continue

        try:
            content = local_path.read_text()
            features = extract_features(url, content, parsed)
            features_list.append(features.to_dict())
        except Exception as e:
            print(f"Error processing {url}: {e}")
            errors += 1

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(urls)} skills...")

    print(f"\nExtracted features from {len(features_list)} skills ({errors} errors)")

    # Create DataFrame and save
    df = pl.DataFrame(features_list)

    # Save to parquet
    output_path = args.output_dir / "skill_features.parquet"
    df.write_parquet(output_path)
    print(f"Saved to {output_path}")

    # Print summary stats
    print("\n=== Summary Statistics ===")
    print(f"Total skills: {len(df)}")
    print(f"With frontmatter: {df['has_frontmatter'].sum()}")
    print(f"With name field: {df['has_name'].sum()}")
    print(f"With description: {df['has_description'].sum()}")
    print(f"With triggers: {df['has_triggers'].sum()}")
    print(f"With examples: {df['has_examples'].sum()}")
    print(f"\nByte size: min={df['byte_size'].min()}, max={df['byte_size'].max()}, median={df['byte_size'].median()}")
    print(f"Line count: min={df['line_count'].min()}, max={df['line_count'].max()}, median={df['line_count'].median()}")


