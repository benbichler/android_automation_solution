import json
import tempfile
import unittest
from pathlib import Path

from android_runner.config import ConfigError, load_config


def dump_config(directory, payload):
    path = Path(directory) / "config.json"
    if isinstance(payload, str):
        path.write_text(payload)
    else:
        path.write_text(json.dumps(payload))
    return path


class LoadConfigTest(unittest.TestCase):
    def test_project_config(self):
        config = load_config("config.json")
        self.assertEqual(config.package_name, "com.android.settings")
        self.assertEqual(config.minimum_android_version, 10)
        self.assertEqual(config.minimum_battery, 20)
        self.assertIsNone(config.device_id)

    def test_device_id_is_stripped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = dump_config(directory, {
                "package_name": "com.android.settings",
                "minimum_android_version": 10,
                "minimum_battery": 20,
                "device_id": " emulator-5554 ",
            })
            config = load_config(path)
        self.assertEqual(config.device_id, "emulator-5554")

    def test_ten_point_zero_counts_as_ten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = dump_config(directory, {
                "package_name": "com.android.settings",
                "minimum_android_version": 10.0,
                "minimum_battery": 20.0,
            })
            config = load_config(path)
        self.assertEqual(config.minimum_android_version, 10)
        self.assertEqual(config.minimum_battery, 20)

    def test_missing_file(self):
        with self.assertRaises(ConfigError) as caught:
            load_config("no-such-file.json")
        self.assertIn("not found", str(caught.exception))

    def test_broken_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = dump_config(directory, "{ nope")
            with self.assertRaises(ConfigError) as caught:
                load_config(path)
        self.assertIn("not valid JSON", str(caught.exception))

    def test_missing_package_name(self):
        self._rejects({"minimum_android_version": 10, "minimum_battery": 20}, "package_name")

    def test_package_name_needs_a_dot(self):
        self._rejects({
            "package_name": "settings",
            "minimum_android_version": 10,
            "minimum_battery": 20,
        }, "package_name")

    def test_missing_version(self):
        self._rejects({
            "package_name": "com.android.settings",
            "minimum_battery": 20,
        }, "minimum_android_version")

    def test_true_is_not_a_version(self):
        self._rejects({
            "package_name": "com.android.settings",
            "minimum_android_version": True,
            "minimum_battery": 20,
        }, "minimum_android_version")

    def test_battery_over_100(self):
        self._rejects({
            "package_name": "com.android.settings",
            "minimum_android_version": 10,
            "minimum_battery": 101,
        }, "minimum_battery")

    def test_blank_device_id(self):
        self._rejects({
            "package_name": "com.android.settings",
            "minimum_android_version": 10,
            "minimum_battery": 20,
            "device_id": "  ",
        }, "device_id")

    def _rejects(self, payload, field):
        with tempfile.TemporaryDirectory() as directory:
            path = dump_config(directory, payload)
            with self.assertRaises(ConfigError) as caught:
                load_config(path)
        self.assertIn(field, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
