"""JSON formatter for lint results."""

import json

from .types import LintFinding, LintResult


def format_json(result: LintResult) -> str:
    """Format lint results as JSON.

    Args:
        result: The lint result to format

    Returns:
        JSON string
    """

    def finding_to_dict(f: LintFinding) -> dict:
        d = {
            "rule_id": f.rule_id,
            "message": f.message,
            "severity": f.severity.value,
        }
        if f.line is not None:
            d["line"] = f.line
        if f.suggestion:
            d["suggestion"] = f.suggestion
        return d

    output = {
        "path": str(result.path),
        "findings": [finding_to_dict(f) for f in result.findings],
        "summary": {
            "errors": result.error_count,
            "warnings": result.warning_count,
            "suggestions": result.suggestion_count,
            "total": len(result.findings),
        },
    }

    return json.dumps(output, indent=2)
