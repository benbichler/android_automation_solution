from unittest.mock import patch

import pytest

from android_runner.config import Config
from android_runner.runner import DeviceError, select_device


def config(device_id=None):
    return Config("com.android.settings", 10, 20, device_id)


def devices(*rows):
    return 0, "\n".join(["List of devices attached", *rows]) + "\n", ""


def select(output, device_id=None):
    with patch("android_runner.runner.run_adb", return_value=output):
        return select_device(config(device_id))


def test_one_ready_device():
    assert select(devices("emulator-5554\tdevice")) == "emulator-5554"


def test_device_id_picks_one_of_two():
    output = devices("emulator-5554\tdevice", "R5CT123\tdevice")
    assert select(output, "R5CT123") == "R5CT123"


@pytest.mark.parametrize("rows, device_id, message", [
    ((), None, "No Android device"),
    (("R5CT123\tunauthorized",), None, "R5CT123 is unauthorized"),
    (("emulator-5554\toffline",), None, "emulator-5554 is offline"),
    (("emulator-5554\tdevice", "R5CT123\tdevice"), None, "device_id"),
    (("emulator-5554\tdevice",), "R5CT123", "R5CT123"),
    (("R5CT123\tunauthorized",), "R5CT123", "R5CT123 is unauthorized"),
])
def test_device_problems_are_explained(rows, device_id, message):
    with pytest.raises(DeviceError, match=message):
        select(devices(*rows), device_id)
