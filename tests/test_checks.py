from unittest.mock import patch

import pytest

from android_runner.adb import AdbError
from android_runner.config import Config
from android_runner.runner import check_battery, check_version, collect_device_info, run_checks

SERIAL = "emulator-5554"
STARTED = (0, "Starting: Intent { pkg=com.android.settings }\n", "")
INSTALLED = (0, "package:/data/app/settings/base.apk\n", "")


def config(minimum_battery=20, package_name="com.android.settings"):
    return Config(package_name, 10, minimum_battery)


def fake_adb(version="17\n", battery="  level: 100\n  scale: 100\n", pm=INSTALLED, am=STARTED):
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
            return 0, battery, ""
        if "echo" in args:
            return 0, "hello\n", ""
        if "pm" in args:
            return pm
        if "am" in args:
            return am
        raise AssertionError(args)

    run.calls = calls
    return run


def run_all(fake, cfg=None):
    with patch("android_runner.runner.run_adb", fake):
        info = collect_device_info(SERIAL)
        return run_checks(SERIAL, cfg or config(), info)


def statuses(results):
    return [item["status"] for item in results]


def test_reads_the_five_facts():
    with patch("android_runner.runner.run_adb", fake_adb()):
        info = collect_device_info(SERIAL)
    assert info == {
        "serial": SERIAL,
        "android_version": "17",
        "model": "sdk_gphone16k_arm64",
        "manufacturer": "Google",
        "battery": 100,
    }


def test_strange_battery_output_is_none():
    with patch("android_runner.runner.run_adb", fake_adb(battery="  level: unknown\n")):
        assert collect_device_info(SERIAL)["battery"] is None


def test_all_pass():
    assert statuses(run_all(fake_adb())) == ["PASS"] * 5


@pytest.mark.parametrize("version, expected", [
    ("17", "PASS"),
    ("10", "PASS"),
    ("8.1.0", "FAIL"),
    ("Baklava", "FAIL"),
    (None, "FAIL"),
])
def test_version(version, expected):
    assert check_version({"android_version": version}, config())["status"] == expected


@pytest.mark.parametrize("level, expected", [
    (100, "PASS"),
    (21, "PASS"),
    (20, "FAIL"),
    (0, "FAIL"),
    (None, "FAIL"),
])
def test_battery_is_strictly_above_the_threshold(level, expected):
    assert check_battery({"battery": level}, config(minimum_battery=20))["status"] == expected


def test_missing_package_skips_launch():
    fake = fake_adb(pm=(1, "", ""))
    results = run_all(fake, config(package_name="com.example.missing"))
    assert statuses(results)[3:] == ["FAIL", "SKIP"]
    assert not any("am" in call for call in fake.calls)


def test_starting_plus_error_is_a_fail():
    output = "Starting: Intent { pkg=com.example.demo }\nError: Activity not started\n"
    launch = run_all(fake_adb(am=(0, output, "")))[4]
    assert launch["status"] == "FAIL"
    assert "Error" in launch["detail"]


def test_timeout_fails_one_check_and_continues():
    normal = fake_adb()

    def run(args, timeout=15):
        if "echo" in args:
            raise AdbError("adb timed out after 15s")
        return normal(args, timeout)

    results = run_all(run)
    assert results[0]["status"] == "FAIL"
    assert "timed out" in results[0]["detail"]
    assert statuses(results)[1:] == ["PASS"] * 4


def test_timeout_during_install_check_skips_launch():
    normal = fake_adb()

    def run(args, timeout=15):
        if "pm" in args:
            raise AdbError("adb timed out after 15s")
        return normal(args, timeout)

    assert statuses(run_all(run))[3:] == ["FAIL", "SKIP"]
