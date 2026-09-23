from unittest.mock import patch

import pytest

import main
from android_runner.adb import AdbError
from android_runner.config import Config, ConfigError

INFO = {
    "serial": "emulator-5554",
    "android_version": "17",
    "model": "sdk_gphone16k_arm64",
    "manufacturer": "Google",
    "battery": 100,
}


def result(status):
    return {"name": "Battery level", "status": status, "detail": "x"}


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("main.load_config", return_value=Config("com.android.settings", 10, 20)), \
         patch("main.select_device", return_value="emulator-5554"), \
         patch("main.collect_device_info", return_value=INFO), \
         patch("main.save_failure_log", return_value="logs/x.log") as save_log, \
         patch("main.run_checks") as run_checks:
        yield run_checks, save_log


def test_all_pass_exits_0(pipeline):
    run_checks, save_log = pipeline
    run_checks.return_value = [result("PASS"), result("SKIP")]
    assert main.main() == 0
    save_log.assert_not_called()


def test_a_failed_check_exits_1_and_saves_a_log(pipeline):
    run_checks, save_log = pipeline
    run_checks.return_value = [result("PASS"), result("FAIL")]
    assert main.main() == 1
    save_log.assert_called_once_with("emulator-5554", "Battery level")


@pytest.mark.parametrize("error", [ConfigError("bad"), AdbError("no adb")])
def test_setup_problem_exits_2(error, capsys):
    with patch("main.load_config", side_effect=error):
        assert main.main() == 2
    assert str(error) in capsys.readouterr().out
