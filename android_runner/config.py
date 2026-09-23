import json
from pathlib import Path


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, package_name, minimum_android_version, minimum_battery, device_id=None):
        self.package_name = package_name
        self.minimum_android_version = minimum_android_version
        self.minimum_battery = minimum_battery
        self.device_id = device_id


def load_config(path): # loading config.json and initializing it all
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid configuration: {path.name} is not valid JSON ({exc.msg})")

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid configuration: {path.name} must be a JSON object")

    package_name = data.get("package_name")
    if not isinstance(package_name, str) or not package_name.strip():
        raise ConfigError("Invalid configuration: missing or invalid field 'package_name'")
    package_name = package_name.strip()
    if "." not in package_name:
        raise ConfigError(
            "Invalid configuration: field 'package_name' must look like 'com.example.demo'"
        )

    version = _whole_number(data, "minimum_android_version", 1, 100)
    battery = _whole_number(data, "minimum_battery", 0, 100)

    device_id = data.get("device_id")
    if device_id is not None:
        if not isinstance(device_id, str) or not device_id.strip():
            raise ConfigError("Invalid configuration: field 'device_id' must be a non-empty string")
        device_id = device_id.strip()

    return Config(package_name, version, battery, device_id)


def _whole_number(data, field, low, high):
    if field not in data:
        raise ConfigError(f"Invalid configuration: missing field '{field}'")
    value = data[field]

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"Invalid configuration: field '{field}' must be a whole number")
    if isinstance(value, float) and not value.is_integer():
        raise ConfigError(f"Invalid configuration: field '{field}' must be a whole number")

    value = int(value)
    if value < low or value > high:
        raise ConfigError(f"Invalid configuration: field '{field}' must be between {low} and {high}")
    return value
