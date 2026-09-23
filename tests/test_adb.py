import subprocess
from unittest.mock import patch

import pytest

from android_runner.adb import AdbError, run_adb


@pytest.fixture
def adb_on_path():
    with patch("android_runner.adb.shutil.which", return_value="/usr/bin/adb"):
        yield


def test_adb_missing():
    with patch("android_runner.adb.shutil.which", return_value=None):
        with pytest.raises(AdbError, match="Platform Tools.*PATH"):
            run_adb(["devices"])


def test_command_is_passed_as_a_list(adb_on_path):
    completed = subprocess.CompletedProcess(["adb"], 0, stdout="hello\n", stderr="")
    with patch("android_runner.adb.subprocess.run", return_value=completed) as run:
        result = run_adb(["shell", "echo", "hello"])

    assert result == (0, "hello\n", "")
    run.assert_called_once_with(
        ["adb", "shell", "echo", "hello"],
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_timeout(adb_on_path):
    expired = subprocess.TimeoutExpired(["adb"], 5)
    with patch("android_runner.adb.subprocess.run", side_effect=expired):
        with pytest.raises(AdbError, match="timed out"):
            run_adb(["shell", "echo", "hello"], timeout=5)


def test_nonzero_exit_is_returned(adb_on_path):
    completed = subprocess.CompletedProcess(["adb"], 1, stdout="", stderr="")
    with patch("android_runner.adb.subprocess.run", return_value=completed):
        assert run_adb(["shell", "pm", "path", "com.missing.app"]) == (1, "", "")
