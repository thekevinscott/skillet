import os
from pathlib import Path

SKILLET_DIR = Path(os.environ.get("SKILLET_DIR", str(Path.home() / ".skillet")))
CACHE_DIR = SKILLET_DIR / "cache"

# Default tools to allow when evaluating with a skill
# SlashCommand is needed to recognize /command syntax in prompts
DEFAULT_SKILL_TOOLS = ["Skill", "SlashCommand", "Bash", "Read", "Write", "WebFetch"]
