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
    """Run a setup or teardown script with the isolated HOME.

    Args:
        script: Shell script to execute
        home_dir: HOME directory to use
        cwd: Working directory for script execution
        timeout: Maximum time in seconds before killing the script

    Returns:
        Tuple of (return_code, stdout, stderr)
        Returns (-1, "", error_message) on timeout
    """
    env = os.environ.copy()
    env["HOME"] = home_dir

    try:
        result = subprocess.run(
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
