"""Extract code examples from markdown content."""

import re


def extract_examples(body: str) -> list[str]:
    """Extract code examples from the skill body."""
    # Find code blocks (```...```)
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", body, re.DOTALL)
    return list(code_blocks)
