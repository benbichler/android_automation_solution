import unittest
from unittest.mock import patch

from android_runner.adb import AdbError
from android_runner.config import Config
from android_runner.runner import collect_device_info, run_checks

SERIAL = "emulator-5554"


def config(minimum_battery=20, package_name="com.android.settings"):
    return Config(package_name, 10, minimum_battery)


def fake_adb(version="17\n", pm=(0, "package:/data/app/settings/base.apk\n", ""), am=None):
    if am is None:
        am = (0, "Starting: Intent { pkg=com.android.settings }\n", "")
    calls = []

    def run(args, timeout=15):
        calls.append(args)
        if "ro.build.version.release" in args:
            return 0, version, ""
        if "ro.product.model" in args:
            return 0, "sdk_gphone16k_arm64\n", ""
        if "ro.product.manufacturer" in args:
            return 0, "Google\n", ""
        if "dumpsys" in args:
            return 0, "  level: 100\n  scale: 100\n", ""
        if "echo" in args:
            return 0, "hello\n", ""
        if "pm" in args:
            return pm
        if "am" in args:
            return am
        raise AssertionError(args)

    run.calls = calls
    return run


class DeviceInfoTest(unittest.TestCase):
    def test_reads_the_five_facts(self):
        with patch("android_runner.runner.run_adb", fake_adb()):
            info = collect_device_info(SERIAL)
        self.assertEqual(info["serial"], SERIAL)
        self.assertEqual(info["android_version"], "17")
        self.assertEqual(info["model"], "sdk_gphone16k_arm64")
        self.assertEqual(info["manufacturer"], "Google")
        self.assertEqual(info["battery"], 100)

    def test_strange_battery_output_is_none(self):
        def run(args, timeout=15):
            if "dumpsys" in args:
                return 0, "  level: unknown\n", ""
            return fake_adb()(args, timeout)

        with patch("android_runner.runner.run_adb", run):
            info = collect_device_info(SERIAL)
        self.assertIsNone(info["battery"])


class RunChecksTest(unittest.TestCase):
    def test_all_pass(self):
        with patch("android_runner.runner.run_adb", fake_adb()):
            info = collect_device_info(SERIAL)
            results = run_checks(SERIAL, config(), info)
        self.assertEqual(
            [item["status"] for item in results],
            ["PASS", "PASS", "PASS", "PASS", "PASS"],
        )

    def test_old_release_uses_the_major_number(self):
        with patch("android_runner.runner.run_adb", fake_adb(version="8.1.0\n")):
            info = collect_device_info(SERIAL)
            version = run_checks(SERIAL, config(), info)[1]
        self.assertEqual(version["status"], "FAIL")
        self.assertIn("8", version["detail"])

    def test_battery_equal_to_the_threshold_fails(self):
        info = {
            "serial": SERIAL,
            "android_version": "17",
            "model": "sdk_gphone16k_arm64",
            "manufacturer": "Google",
            "battery": 20,
        }
        with patch("android_runner.runner.run_adb", fake_adb()):
            battery = run_checks(SERIAL, config(minimum_battery=20), info)[2]
        self.assertEqual(battery["status"], "FAIL")
        self.assertIn("strictly above", battery["detail"])

    def test_missing_package_skips_launch(self):
        fake = fake_adb(pm=(1, "", ""))
        with patch("android_runner.runner.run_adb", fake):
            info = collect_device_info(SERIAL)
            results = run_checks(SERIAL, config(package_name="com.example.missing"), info)
        self.assertEqual(results[3]["status"], "FAIL")
        self.assertEqual(results[4]["status"], "SKIP")
        launched = any("am" in call for call in fake.calls)
        self.assertFalse(launched)

    def test_starting_plus_error_is_a_fail(self):
        output = "Starting: Intent { pkg=com.example.demo }\nError: Activity not started\n"
        with patch("android_runner.runner.run_adb", fake_adb(am=(0, output, ""))):
            info = collect_device_info(SERIAL)
            launch = run_checks(SERIAL, config(), info)[4]
        self.assertEqual(launch["status"], "FAIL")
        self.assertIn("Error", launch["detail"])

    def test_timeout_fails_one_check_and_continues(self):
        def run(args, timeout=15):
            if "echo" in args:
                raise AdbError("adb timed out after 15s")
            return fake_adb()(args, timeout)

        info = {
            "serial": SERIAL,
            "android_version": "17",
            "model": "sdk_gphone16k_arm64",
            "manufacturer": "Google",
            "battery": 100,
        }
        with patch("android_runner.runner.run_adb", run):
            results = run_checks(SERIAL, config(), info)
        self.assertEqual(results[0]["status"], "FAIL")
        self.assertIn("timed out", results[0]["detail"])
        self.assertEqual([item["status"] for item in results[1:]], ["PASS", "PASS", "PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
