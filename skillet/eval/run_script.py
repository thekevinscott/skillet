"""Run setup/teardown scripts with isolated HOME."""

import os
import subprocess


def run_script(script: str, home_dir: str, cwd: str | None = None) -> tuple[int, str, str]:
    """Run a setup or teardown script with the isolated HOME.

    Args:
        script: Shell script to execute
        home_dir: HOME directory to use
        cwd: Working directory for script execution

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    env = os.environ.copy()
    env["HOME"] = home_dir

    result = subprocess.run(
        ["bash", "-c", script],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout, result.stderr
