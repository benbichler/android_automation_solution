import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from android_runner.adb import AdbError
from android_runner.report import save_failure_log, write_report


def info():
    return {
        "serial": "emulator-5554",
        "android_version": "17",
        "model": "sdk_gphone16k_arm64",
        "manufacturer": "Google",
        "battery": 100,
    }


def check(name, status, detail="ok", log=None):
    item = {"name": name, "status": status, "detail": detail}
    if log:
        item["log"] = log
    return item


class WriteReportTest(unittest.TestCase):
    def test_pass_when_nothing_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            results = [
                check("Device is reachable", "PASS"),
                check("Launch application", "SKIP", "not installed"),
            ]
            overall = write_report(info(), results, path)
            text = path.read_text()
        self.assertEqual(overall, "PASS")
        self.assertIn("ID: emulator-5554", text)
        self.assertIn("Passed: 1", text)
        self.assertIn("Failed: 0", text)
        self.assertIn("Skipped: 1", text)
        self.assertIn("All: 2", text)
        self.assertIn("Overall: PASS", text)

    def test_fail_when_one_check_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            results = [
                check("Battery level", "FAIL", "Battery is 20%, and the threshold is strictly above 20%."),
                check("Device is reachable", "PASS"),
            ]
            overall = write_report(info(), results, path)
            text = path.read_text()
        self.assertEqual(overall, "FAIL")
        self.assertIn("Battery level: FAIL", text)
        self.assertIn("Overall: FAIL", text)


class SaveFailureLogTest(unittest.TestCase):
    def test_writes_logcat_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("android_runner.report.run_adb", return_value=(0, "log line\n", "")):
                saved = save_failure_log("emulator-5554", "Battery level", directory)
            self.assertIsNotNone(saved)
            self.assertIn("battery_level", saved)
            self.assertEqual(Path(saved).read_text(), "log line\n")

    def test_logcat_problem_does_not_raise(self):
        with patch("android_runner.report.run_adb", side_effect=AdbError("timed out")):
            saved = save_failure_log("emulator-5554", "Battery level")
        self.assertIsNone(saved)


if __name__ == "__main__":
    unittest.main()
