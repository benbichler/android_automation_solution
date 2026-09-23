"""Run adb. A non-zero exit comes back to the caller."""

import shutil
import subprocess


class AdbError(Exception):
    pass


def run_adb(args, timeout=15):
    if shutil.which("adb") is None:
        raise AdbError(
            "adb was not found. Install Android SDK Platform Tools and add adb to PATH."
        )

    command = ["adb", *args]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AdbError(f"adb timed out after {timeout}s: {' '.join(command)}")
    except FileNotFoundError:
        raise AdbError(
            "adb was not found. Install Android SDK Platform Tools and add adb to PATH."
        )

    return completed.returncode, completed.stdout, completed.stderr
