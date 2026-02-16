"""Tests for check_regex."""

from skillet.eval.judge.run_assertions.check_regex import check_regex


def describe_check_regex():
    def it_passes_when_pattern_matches():
        assert check_regex(r"\d+", response="the answer is 42") is None

    def it_fails_when_pattern_does_not_match():
        result = check_regex(r"^\d+$", response="no numbers here")
        assert result is not None
        assert "did not match" in result

    def it_handles_invalid_regex():
        result = check_regex("[invalid", response="test")
        assert result is not None
        assert "invalid pattern" in result

    def it_supports_case_insensitive_flag():
        assert check_regex("(?i)hello", response="HELLO world") is None
