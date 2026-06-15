"""Tests for skillet.config."""

import importlib
import os
from pathlib import Path
from unittest.mock import patch

from skillet import config


def describe_config():
    def it_derives_cache_dir_from_skillet_dir():
        assert config.CACHE_DIR == config.SKILLET_DIR / "cache"

    def it_honors_skillet_dir_env_override():
        with patch.dict(os.environ, {"SKILLET_DIR": "/tmp/custom-skillet"}):
            importlib.reload(config)
            try:
                assert Path("/tmp/custom-skillet") == config.SKILLET_DIR
                assert Path("/tmp/custom-skillet/cache") == config.CACHE_DIR
            finally:
                importlib.reload(config)

    def it_defaults_skillet_dir_to_home_when_unset():
        env_without = {k: v for k, v in os.environ.items() if k != "SKILLET_DIR"}
        with patch.dict(os.environ, env_without, clear=True):
            importlib.reload(config)
            try:
                assert Path.home() / ".skillet" == config.SKILLET_DIR
            finally:
                importlib.reload(config)

    def it_includes_core_default_skill_tools():
        assert config.DEFAULT_SKILL_TOOLS == [
            "Skill",
            "SlashCommand",
            "Bash",
            "Read",
            "Write",
            "WebFetch",
        ]
