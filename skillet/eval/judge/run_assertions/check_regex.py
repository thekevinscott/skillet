"""Check that response matches a regex pattern."""

import re


def check_regex(value: str, response: str, **_: object) -> str | None:
    try:
        if not re.search(value, response):
            return f"regex: pattern '{value}' did not match"
    except re.error as e:
        return f"regex: invalid pattern '{value}': {e}"
    return None
