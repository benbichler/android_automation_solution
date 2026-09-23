import subprocess
import unittest
from unittest.mock import patch

from android_runner.adb import AdbError, run_adb


class RunAdbTest(unittest.TestCase):
    def test_adb_missing(self):
        with patch("android_runner.adb.shutil.which", return_value=None):
            with self.assertRaises(AdbError) as caught:
                run_adb(["devices"])
        message = str(caught.exception)
        self.assertIn("Platform Tools", message)
        self.assertIn("PATH", message)

    def test_command_is_passed_as_a_list(self):
        completed = subprocess.CompletedProcess(
            ["adb", "shell", "echo", "hello"], 0, stdout="hello\n", stderr=""
        )
        with patch("android_runner.adb.shutil.which", return_value="/usr/bin/adb"):
            with patch("android_runner.adb.subprocess.run", return_value=completed) as run:
                code, out, err = run_adb(["shell", "echo", "hello"])

        self.assertEqual((code, out, err), (0, "hello\n", ""))
        run.assert_called_once_with(
            ["adb", "shell", "echo", "hello"],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_timeout(self):
        expired = subprocess.TimeoutExpired(["adb", "shell", "echo", "hello"], 5)
        with patch("android_runner.adb.shutil.which", return_value="/usr/bin/adb"):
            with patch("android_runner.adb.subprocess.run", side_effect=expired):
                with self.assertRaises(AdbError) as caught:
                    run_adb(["shell", "echo", "hello"], timeout=5)
        self.assertIn("timed out", str(caught.exception))

    def test_nonzero_exit_is_returned(self):
        completed = subprocess.CompletedProcess(
            ["adb", "shell", "pm", "path", "com.missing.app"], 1, stdout="", stderr=""
        )
        with patch("android_runner.adb.shutil.which", return_value="/usr/bin/adb"):
            with patch("android_runner.adb.subprocess.run", return_value=completed):
                code, out, err = run_adb(["shell", "pm", "path", "com.missing.app"])
        self.assertEqual((code, out, err), (1, "", ""))


if __name__ == "__main__":
    unittest.main()
