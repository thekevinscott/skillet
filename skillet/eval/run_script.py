"""Run setup/teardown scripts with isolated HOME."""

import os
import subprocess

# Default timeout for script execution (in seconds)
DEFAULT_SCRIPT_TIMEOUT = 30


def run_script(
    script: str,
    home_dir: str,
    cwd: str | None = None,
    timeout: int = DEFAULT_SCRIPT_TIMEOUT,
) -> tuple[int, str, str]:
    """Run a setup or teardown script with the isolated HOME."""
    env = os.environ.copy()
    env["HOME"] = home_dir

    try:
        result = subprocess.run(  # nosec B603 B607
            ["bash", "-c", script],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return (-1, "", f"Script timed out after {timeout}s")
