"""Read config.json. Raise ConfigError with a plain message if it's bad."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

# com.example.app — at least two segments, each starting with a letter.
PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")


class ConfigError(Exception):
    pass


@dataclass
class Config:
    package_name: str
    minimum_android_version: int
    minimum_battery: int
    device_id: str | None = None


def load_config(path) -> Config:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid configuration: {path.name} is not valid JSON ({exc.msg})")

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid configuration: {path.name} must be a JSON object")

    package_name = str(data.get("package_name", "")).strip()
    if not package_name:
        raise ConfigError("Invalid configuration: missing or invalid field 'package_name'")
    if PACKAGE_RE.fullmatch(package_name) is None:
        raise ConfigError(
            "Invalid configuration: field 'package_name' must look like 'com.example.demo'"
        )

    device_id = data.get("device_id")
    if device_id is not None:
        if not isinstance(device_id, str) or not device_id.strip():
            raise ConfigError("Invalid configuration: field 'device_id' must be a non-empty string")
        device_id = device_id.strip()

    return Config(
        package_name=package_name,
        minimum_android_version=_whole_number(data, "minimum_android_version", low=1),
        minimum_battery=_whole_number(data, "minimum_battery", low=0, high=100),
        device_id=device_id,
    )


def _whole_number(data, field, low, high=None):
    if field not in data:
        raise ConfigError(f"Invalid configuration: missing field '{field}'")

    value = data[field]
    # JSON true/false become bools, and bool is a subclass of int.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"Invalid configuration: field '{field}' must be a whole number")
    if isinstance(value, float) and not value.is_integer():
        raise ConfigError(f"Invalid configuration: field '{field}' must be a whole number")

    number = int(value)
    if number < low or (high is not None and number > high):
        if high is None:
            bounds = f"at least {low}"
        else:
            bounds = f"between {low} and {high}"
        raise ConfigError(f"Invalid configuration: field '{field}' must be {bounds}")
    return number
