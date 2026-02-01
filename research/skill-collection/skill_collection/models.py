"""Data models and constants for skill collection."""

from dataclasses import dataclass, field

DEFAULT_CHUNK_SIZE = 100  # Default chunk size for subdivision ranges
EXPECTED_TOTAL = 113_066  # Approximate based on GitHub search across all size ranges


@dataclass
class SizeRange:
    """A file size range for sharding queries."""

    min_bytes: int
    max_bytes: int | None = None  # None means no upper bound

    @property
    def width(self) -> int:
        """Width of the range in bytes."""
        if self.max_bytes is None:
            return self.min_bytes  # Use min as width for unbounded
        return self.max_bytes - self.min_bytes

    def to_query_param(self) -> str:
        """Convert to GitHub size qualifier."""
        if self.max_bytes is None:
            return f"size:>={self.min_bytes}"
        return f"size:{self.min_bytes}..{self.max_bytes}"

    def to_search_query(self, filename: str = "SKILL.md") -> str:
        """Build a GitHub code search query for this range."""
        return f"filename:{filename}+{self.to_query_param()}"

    def subdivide(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> tuple["SizeRange", "SizeRange"]:
        """Split into first half and a chunk_size range starting at midpoint.

        For bounded ranges: after multiple subdivisions, the next range always
        uses chunk_size to maintain consistent chunking (rather than progressively
        smaller ranges).

        For unbounded ranges: doubles the starting point (exponential exploration
        for very large files).
        """
        if self.max_bytes is None:
            # Unbounded: use exponential doubling for large files
            mid = self.min_bytes * 2
            return (
                SizeRange(self.min_bytes, mid - 1),
                SizeRange(mid, None),
            )

        mid = self.min_bytes + self.width // 2
        return (
            SizeRange(self.min_bytes, mid),
            SizeRange(mid + 1, mid + chunk_size),
        )

    def __str__(self) -> str:
        if self.max_bytes is None:
            return f">{self.min_bytes}"
        return f"{self.min_bytes}-{self.max_bytes}"


@dataclass
class ProgressRow:
    """A row in the progress table, sortable by min_bytes."""

    min_bytes: int
    max_bytes: int | None
    range_str: str
    total_count: int
    collected: int
    pages: dict[int, int]
    bold: bool = False

    @property
    def width(self) -> int:
        """Width of the range in bytes."""
        if self.max_bytes is None:
            return self.min_bytes  # Use min as width for unbounded
        return self.max_bytes - self.min_bytes

    def format(self) -> str:
        """Format as markdown table row."""
        range_cell = f"**{self.range_str}**" if self.bold else self.range_str
        page_cells = [str(self.pages.get(i, "")) for i in range(1, 11)]
        return f"| {range_cell} | {self.total_count:,} | {self.width:,} | {self.collected:,} | " + " | ".join(page_cells) + " |\n"


@dataclass
class ShardResult:
    """Result of collecting a single shard."""

    range: SizeRange
    total_count: int
    collected: int
    pages: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "range": str(self.range),
            "range_query": self.range.to_query_param(),
            "total_count": self.total_count,
            "collected": self.collected,
            "pages": self.pages,
        }

    def to_progress_row(self, bold: bool = False) -> ProgressRow:
        """Convert to a progress row for display."""
        return ProgressRow(
            min_bytes=self.range.min_bytes,
            max_bytes=self.range.max_bytes,
            range_str=str(self.range),
            total_count=self.total_count,
            collected=self.collected,
            pages=self.pages,
            bold=bold,
        )


# Size ranges chosen to keep each shard under 1000 results
SIZE_RANGES = [
    SizeRange(0, 99),
    SizeRange(100, 199),
    SizeRange(200, 299),
    SizeRange(300, 399),
    SizeRange(400, 499),
    SizeRange(500, 599),
    SizeRange(600, 699),
    SizeRange(700, 799),
    SizeRange(800, 899),
    SizeRange(900, 999),
    SizeRange(1000, 1249),
    SizeRange(1250, 1499),
    SizeRange(1500, 1749),
    SizeRange(1750, 1999),
    SizeRange(2000, 2499),
    SizeRange(2500, 2999),
    SizeRange(3000, 3499),
    SizeRange(3500, 3999),
    SizeRange(4000, 4499),
    SizeRange(4500, 4999),
    SizeRange(5000, 5999),
    SizeRange(6000, 6999),
    SizeRange(7000, 7999),
    SizeRange(8000, 8999),
    SizeRange(9000, 9999),
    SizeRange(10000, 12499),
    SizeRange(12500, 14999),
    SizeRange(15000, 17499),
    SizeRange(17500, 19999),
    SizeRange(20000, 24999),
    SizeRange(25000, 29999),
    SizeRange(30000, 34999),
    SizeRange(35000, 39999),
    SizeRange(40000, 44999),
    SizeRange(45000, 49999),
    SizeRange(50000, 74999),
    SizeRange(75000, 99999),
    SizeRange(100000, None),
]
