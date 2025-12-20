"""Tests for get_scripts_from_evals function."""

from skillet.cli.commands.eval.get_scripts_from_evals import get_scripts_from_evals


def describe_get_scripts_from_evals():
    """Tests for get_scripts_from_evals function."""

    def it_returns_empty_list_for_evals_without_scripts():
        """Evals without setup/teardown return empty list."""
        evals = [
            {"_source": "001.yaml", "prompt": "test", "expected": "result"},
            {"_source": "002.yaml", "prompt": "test2", "expected": "result2"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == []

    def it_extracts_setup_scripts():
        """Setup scripts are extracted with source and type."""
        evals = [
            {"_source": "001.yaml", "setup": "mkdir -p /tmp/test"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == [("001.yaml", "setup", "mkdir -p /tmp/test")]

    def it_extracts_teardown_scripts():
        """Teardown scripts are extracted with source and type."""
        evals = [
            {"_source": "001.yaml", "teardown": "rm -rf /tmp/test"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == [("001.yaml", "teardown", "rm -rf /tmp/test")]

    def it_extracts_both_setup_and_teardown():
        """Both setup and teardown are extracted from same eval."""
        evals = [
            {
                "_source": "001.yaml",
                "setup": "mkdir -p /tmp/test",
                "teardown": "rm -rf /tmp/test",
            },
        ]
        result = get_scripts_from_evals(evals)
        assert len(result) == 2
        assert ("001.yaml", "setup", "mkdir -p /tmp/test") in result
        assert ("001.yaml", "teardown", "rm -rf /tmp/test") in result

    def it_extracts_scripts_from_multiple_evals():
        """Scripts from multiple evals are all extracted."""
        evals = [
            {"_source": "001.yaml", "setup": "echo first"},
            {"_source": "002.yaml", "setup": "echo second"},
            {"_source": "003.yaml", "teardown": "echo third"},
        ]
        result = get_scripts_from_evals(evals)
        assert len(result) == 3

    def it_uses_unknown_source_when_missing():
        """Missing _source defaults to 'unknown'."""
        evals = [{"setup": "echo test"}]
        result = get_scripts_from_evals(evals)
        assert result == [("unknown", "setup", "echo test")]
