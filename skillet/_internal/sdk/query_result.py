"""QueryResult dataclass for SDK query responses."""

from dataclasses import dataclass, field


@dataclass
class QueryResult:
    """Result from a query with both text and tool calls."""

    text: str
    tool_calls: list[dict] = field(default_factory=list)
