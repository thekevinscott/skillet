"""Extract numbered or bulleted items from markdown sections."""

import re


def extract_section_items(body: str, section_name: str) -> list[str]:
    """Extract numbered or bulleted items from a section."""
    items: list[str] = []

    # Find the section (## Goals, ## Prohibitions, etc.)
    pattern = rf"^##\s+{section_name}\s*$"
    match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
    if not match:
        return items

    # Get content from section start to next ## header or end
    section_start = match.end()
    next_section = re.search(r"^##\s+", body[section_start:], re.MULTILINE)
    if next_section:
        section_content = body[section_start : section_start + next_section.start()]
    else:
        section_content = body[section_start:]

    # Extract numbered items (1. item, 2. item)
    numbered = re.findall(r"^\d+\.\s+(.+)$", section_content, re.MULTILINE)
    items.extend(numbered)

    # Extract bulleted items (- item, * item)
    if not items:
        bulleted = re.findall(r"^[-*]\s+(.+)$", section_content, re.MULTILINE)
        items.extend(bulleted)

    return items
