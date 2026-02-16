"""Tests for check_one_function_per_file."""

from pathlib import Path
from textwrap import dedent

import pytest
from check_one_function_per_file import (
    check_directory,
    format_violations,
    get_public_callables,
    has_suppression_comment,
    is_exempt,
)


def describe_get_public_callables():
    def it_returns_single_function():
        source = "def foo(): pass"
        assert get_public_callables(source) == ["foo"]

    def it_returns_single_class():
        source = "class Foo: pass"
        assert get_public_callables(source) == ["Foo"]

    def it_returns_multiple_callables():
        source = dedent("""\
            def foo(): pass
            def bar(): pass
            """)
        assert get_public_callables(source) == ["foo", "bar"]

    def it_excludes_private_functions():
        source = dedent("""\
            def _private(): pass
            def public(): pass
            """)
        assert get_public_callables(source) == ["public"]

    def it_excludes_private_classes():
        source = dedent("""\
            class _Internal: pass
            class Public: pass
            """)
        assert get_public_callables(source) == ["Public"]

    def it_ignores_nested_functions():
        source = dedent("""\
            def outer():
                def inner():
                    pass
            """)
        assert get_public_callables(source) == ["outer"]

    def it_ignores_methods():
        source = dedent("""\
            class Foo:
                def method(self): pass
                def other(self): pass
            """)
        assert get_public_callables(source) == ["Foo"]

    def it_handles_async_functions():
        source = "async def fetch(): pass"
        assert get_public_callables(source) == ["fetch"]

    def it_handles_mixed_async_and_sync():
        source = dedent("""\
            async def fetch(): pass
            def process(): pass
            """)
        assert get_public_callables(source) == ["fetch", "process"]

    def it_ignores_module_level_assignments():
        source = dedent("""\
            CONSTANT = 42
            LicenseFieldRule = _field_rule("license")
            def foo(): pass
            """)
        assert get_public_callables(source) == ["foo"]

    def it_ignores_constants_only():
        source = dedent("""\
            X = 1
            Y = 2
            """)
        assert get_public_callables(source) == []

    def it_returns_empty_on_syntax_error():
        source = "def foo(:"
        assert get_public_callables(source) == []

    def it_returns_empty_for_empty_file():
        assert get_public_callables("") == []


def describe_has_suppression_comment():
    def it_detects_comment_in_first_20_lines():
        lines = ["# line"] * 5 + ["# skillet: allow-multiple-public-callables"] + ["# more"]
        source = "\n".join(lines)
        assert has_suppression_comment(source) is True

    def it_detects_inline_comment():
        source = "FOO = 1  # skillet: allow-multiple-public-callables\ndef foo(): pass"
        assert has_suppression_comment(source) is True

    def it_returns_false_when_absent():
        source = "def foo(): pass\ndef bar(): pass"
        assert has_suppression_comment(source) is False

    def it_returns_false_when_past_line_20():
        lines = ["# line"] * 20 + ["# skillet: allow-multiple-public-callables"]
        source = "\n".join(lines)
        assert has_suppression_comment(source) is False

    def it_detects_at_exactly_line_20():
        lines = ["# line"] * 19 + ["# skillet: allow-multiple-public-callables"]
        source = "\n".join(lines)
        assert has_suppression_comment(source) is True


def describe_is_exempt():
    @pytest.mark.parametrize(
        "filename",
        [
            "__init__.py",
            "conftest.py",
            "types.py",
            "models.py",
            "result.py",
            "errors.py",
            "base.py",
            "config.py",
            "dataclasses.py",
        ],
    )
    def it_exempts_special_filenames(filename):
        assert is_exempt(Path(filename)) is True

    def it_exempts_test_files():
        assert is_exempt(Path("foo_test.py")) is True
        assert is_exempt(Path("bar/baz_test.py")) is True

    def it_exempts_tests_directory():
        assert is_exempt(Path("tests/test_foo.py")) is True
        assert is_exempt(Path("tests/integration/test_bar.py")) is True

    def it_does_not_exempt_regular_files():
        assert is_exempt(Path("foo.py")) is False
        assert is_exempt(Path("bar/baz.py")) is False


def describe_check_directory():
    def it_returns_empty_for_clean_directory(tmp_path):
        (tmp_path / "foo.py").write_text("def foo(): pass\n")
        (tmp_path / "bar.py").write_text("class Bar: pass\n")
        assert check_directory(tmp_path) == {}

    def it_detects_violations(tmp_path):
        (tmp_path / "bad.py").write_text("def foo(): pass\ndef bar(): pass\n")
        violations = check_directory(tmp_path)
        assert Path("bad.py") in violations
        assert violations[Path("bad.py")] == ["foo", "bar"]

    def it_respects_suppression(tmp_path):
        content = dedent("""\
            # skillet: allow-multiple-public-callables
            def foo(): pass
            def bar(): pass
            """)
        (tmp_path / "multi.py").write_text(content)
        assert check_directory(tmp_path) == {}

    def it_skips_exempt_files(tmp_path):
        (tmp_path / "__init__.py").write_text("def foo(): pass\ndef bar(): pass\n")
        (tmp_path / "types.py").write_text("class A: pass\nclass B: pass\n")
        (tmp_path / "foo_test.py").write_text("def test_a(): pass\ndef test_b(): pass\n")
        assert check_directory(tmp_path) == {}

    def it_skips_tests_directory(tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "foo.py").write_text("def a(): pass\ndef b(): pass\n")
        assert check_directory(tmp_path) == {}

    def it_handles_nested_directories(tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "good.py").write_text("def only(): pass\n")
        (sub / "bad.py").write_text("def one(): pass\nclass Two: pass\n")
        violations = check_directory(tmp_path)
        assert Path("sub/bad.py") in violations


def describe_format_violations():
    def it_formats_single_violation():
        violations = {Path("foo.py"): ["bar", "baz"]}
        result = format_violations(violations)
        assert result == "  foo.py: bar, baz"

    def it_formats_multiple_violations():
        violations = {
            Path("a.py"): ["x", "y"],
            Path("b.py"): ["m", "n", "o"],
        }
        result = format_violations(violations)
        assert "a.py: x, y" in result
        assert "b.py: m, n, o" in result
