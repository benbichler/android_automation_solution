import json

import pytest

from android_runner.config import ConfigError, load_config

VALID = {
    "package_name": "com.android.settings",
    "minimum_android_version": 10,
    "minimum_battery": 20,
}


@pytest.fixture
def write_config(tmp_path):
    def write(payload):
        path = tmp_path / "config.json"
        path.write_text(payload if isinstance(payload, str) else json.dumps(payload))
        return path
    return write


def test_project_config():
    config = load_config("config.json")
    assert config.package_name == "com.android.settings"
    assert config.minimum_android_version == 10
    assert config.minimum_battery == 20
    assert config.device_id is None


def test_device_id_is_stripped(write_config):
    config = load_config(write_config({**VALID, "device_id": " emulator-5554 "}))
    assert config.device_id == "emulator-5554"


def test_ten_point_zero_counts_as_ten(write_config):
    config = load_config(write_config({**VALID, "minimum_android_version": 10.0, "minimum_battery": 20.0}))
    assert config.minimum_android_version == 10
    assert config.minimum_battery == 20


def test_missing_file():
    with pytest.raises(ConfigError, match="not found"):
        load_config("no-such-file.json")


def test_broken_json(write_config):
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(write_config("{ nope"))


@pytest.mark.parametrize("change, field", [
    ({"package_name": None}, "package_name"),
    ({"package_name": "settings"}, "package_name"),
    ({"minimum_android_version": None}, "minimum_android_version"),
    ({"minimum_android_version": True}, "minimum_android_version"),
    ({"minimum_android_version": 10.5}, "minimum_android_version"),
    ({"minimum_battery": 101}, "minimum_battery"),
    ({"minimum_battery": -1}, "minimum_battery"),
    ({"minimum_battery": "20"}, "minimum_battery"),
    ({"device_id": "  "}, "device_id"),
])
def test_bad_field_is_named(write_config, change, field):
    payload = {**VALID, **change}
    payload = {key: value for key, value in payload.items() if value is not None}
    with pytest.raises(ConfigError, match=field):
        load_config(write_config(payload))
