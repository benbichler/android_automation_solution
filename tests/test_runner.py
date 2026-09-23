import unittest
from unittest.mock import patch

from android_runner.config import Config
from android_runner.runner import DeviceError, select_device


def config(device_id=None):
    return Config("com.android.settings", 10, 20, device_id)


def devices_text(*rows):
    body = "\n".join(["List of devices attached", *rows])
    return 0, body + "\n", ""


class SelectDeviceTest(unittest.TestCase):
    def test_one_ready_device(self):
        output = devices_text("emulator-5554\tdevice")
        with patch("android_runner.runner.run_adb", return_value=output):
            serial = select_device(config())
        self.assertEqual(serial, "emulator-5554")

    def test_no_device(self):
        with patch("android_runner.runner.run_adb", return_value=devices_text()):
            with self.assertRaises(DeviceError) as caught:
                select_device(config())
        self.assertIn("No Android device", str(caught.exception))

    def test_unauthorized(self):
        output = devices_text("R5CT123\tunauthorized")
        with patch("android_runner.runner.run_adb", return_value=output):
            with self.assertRaises(DeviceError) as caught:
                select_device(config())
        message = str(caught.exception)
        self.assertIn("R5CT123", message)
        self.assertIn("unauthorized", message)

    def test_offline(self):
        output = devices_text("emulator-5554\toffline")
        with patch("android_runner.runner.run_adb", return_value=output):
            with self.assertRaises(DeviceError) as caught:
                select_device(config())
        self.assertIn("emulator-5554 is offline", str(caught.exception))

    def test_two_devices_need_an_id(self):
        output = devices_text("emulator-5554\tdevice", "R5CT123\tdevice")
        with patch("android_runner.runner.run_adb", return_value=output):
            with self.assertRaises(DeviceError) as caught:
                select_device(config())
        self.assertIn("device_id", str(caught.exception))

    def test_device_id_picks_one_of_two(self):
        output = devices_text("emulator-5554\tdevice", "R5CT123\tdevice")
        with patch("android_runner.runner.run_adb", return_value=output):
            serial = select_device(config("R5CT123"))
        self.assertEqual(serial, "R5CT123")

    def test_device_id_not_connected(self):
        output = devices_text("emulator-5554\tdevice")
        with patch("android_runner.runner.run_adb", return_value=output):
            with self.assertRaises(DeviceError) as caught:
                select_device(config("R5CT123"))
        self.assertIn("R5CT123", str(caught.exception))

    def test_chosen_device_is_unauthorized(self):
        output = devices_text("R5CT123\tunauthorized")
        with patch("android_runner.runner.run_adb", return_value=output):
            with self.assertRaises(DeviceError) as caught:
                select_device(config("R5CT123"))
        self.assertIn("R5CT123 is unauthorized", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
