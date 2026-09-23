from unittest.mock import patch

from android_runner.adb import AdbError
from android_runner.report import save_failure_log, write_report

INFO = {
    "serial": "emulator-5554",
    "android_version": "17",
    "model": "sdk_gphone16k_arm64",
    "manufacturer": "Google",
    "battery": 100,
}


def check(name, status, detail="ok"):
    return {"name": name, "status": status, "detail": detail}


def test_pass_when_nothing_failed(tmp_path):
    path = tmp_path / "report.txt"
    results = [check("Device is reachable", "PASS"), check("Launch application", "SKIP")]

    assert write_report(INFO, results, path) == "PASS"
    text = path.read_text()
    for line in ["ID: emulator-5554", "Passed: 1", "Failed: 0", "Skipped: 1", "All: 2", "Overall: PASS"]:
        assert line in text


def test_fail_when_one_check_failed(tmp_path):
    path = tmp_path / "report.txt"
    results = [check("Battery level", "FAIL"), check("Device is reachable", "PASS")]

    assert write_report(INFO, results, path) == "FAIL"
    text = path.read_text()
    assert "Battery level: FAIL" in text
    assert "Overall: FAIL" in text


def test_log_path_goes_into_the_report(tmp_path):
    path = tmp_path / "report.txt"
    item = {**check("Battery level", "FAIL"), "log": "logs/x_battery_level.log"}
    write_report(INFO, [item], path)
    assert "Log: logs/x_battery_level.log" in path.read_text()


def test_writes_logcat_output(tmp_path):
    with patch("android_runner.report.run_adb", return_value=(0, "log line\n", "")):
        saved = save_failure_log("emulator-5554", "Battery level", tmp_path)
    assert "battery_level" in saved
    assert open(saved).read() == "log line\n"


def test_logcat_problem_does_not_raise(tmp_path):
    with patch("android_runner.report.run_adb", side_effect=AdbError("timed out")):
        assert save_failure_log("emulator-5554", "Battery level", tmp_path) is None
