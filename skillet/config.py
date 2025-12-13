from pathlib import Path

SKILLET_DIR = Path.home() / ".skillet"
CACHE_DIR = SKILLET_DIR / "cache"

# Default tools to allow when evaluating with a skill
DEFAULT_SKILL_TOOLS = ["Skill", "Bash", "Read", "Write", "WebFetch"]

# Maximum lines for generated SKILL.md files
MAX_SKILL_LINES = 50
