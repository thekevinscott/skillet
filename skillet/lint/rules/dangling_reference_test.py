"""Tests for dangling reference rule."""

from pathlib import Path

from skillet.lint.rules.dangling_reference import DanglingReferenceRule
from skillet.lint.types import LintSeverity, SkillDocument


def make_doc(body: str, skill_dir: Path) -> SkillDocument:
    """Create a SkillDocument with body content in a specific directory."""
    skill_path = skill_dir / "SKILL.md"
    frontmatter = "---\nname: test\ndescription: test\n---\n"
    content = frontmatter + body
    return SkillDocument(
        path=skill_path,
        content=content,
        frontmatter={"name": "test", "description": "test"},
        body=body,
        line_count=len(content.splitlines()),
        frontmatter_end_line=4,
    )


def describe_dangling_reference_rule():
    """Tests for DanglingReferenceRule."""

    def it_passes_when_no_references(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("No file references here.", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_passes_for_existing_file_references(tmp_path: Path):
        rule = DanglingReferenceRule()
        # Create the referenced file
        (tmp_path / "helper.py").write_text("# helper")
        doc = make_doc("See [helper](helper.py) for details.", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_warns_for_missing_markdown_link_targets(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("See [docs](missing.md) for details.", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].severity == LintSeverity.WARNING
        assert "missing.md" in findings[0].message

    def it_warns_for_missing_backtick_references(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("Check `config.yaml` for settings.", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "config.yaml" in findings[0].message

    def it_ignores_http_urls(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc(
            "See [docs](https://example.com/docs.md) for details.\n"
            "Also [http link](http://example.com/file.txt).",
            tmp_path,
        )

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_ignores_anchor_links(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("See [section](#installation) below.", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_ignores_mailto_links(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("Contact [support](mailto:help@example.com).", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 0

    def it_reports_line_numbers(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc(
            "Line one.\n"
            "Line two.\n"
            "See [missing](missing.md).\n"
            "Line four.",
            tmp_path,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        # Line 7 = 4 frontmatter + 3rd body line
        assert findings[0].line == 7

    def it_handles_relative_paths(tmp_path: Path):
        rule = DanglingReferenceRule()
        # Create subdirectory with file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "exists.md").write_text("# exists")

        doc = make_doc(
            "Exists: [doc](subdir/exists.md)\n"
            "Missing: [doc](subdir/missing.md)",
            tmp_path,
        )

        findings = rule.check(doc)

        assert len(findings) == 1
        assert "missing.md" in findings[0].message

    def it_provides_suggestions(tmp_path: Path):
        rule = DanglingReferenceRule()
        doc = make_doc("See [docs](missing.md).", tmp_path)

        findings = rule.check(doc)

        assert len(findings) == 1
        assert findings[0].suggestion is not None
