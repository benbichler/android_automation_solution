# Android Python Automation

A command-line tool that uses Android Debug Bridge to inspect one Android device or emulator, run five checks, and write `report.txt`.

Config loading is implemented. The other modules are still placeholders.

## Layout

| Path | Role |
|---|---|
| `main.py` | Runs the steps in order and exits with a clear message. |
| `config.json` | Package name and the two thresholds. Edit this, not the Python. |
| `android_runner/config.py` | Loads and validates the config before ADB is contacted. |
| `android_runner/adb.py` | Finds `adb` and runs one command with a timeout. |
| `android_runner/runner.py` | Picks one device and runs the five checks. |
| `android_runner/report.py` | Writes `report.txt` and saves `logs/` when a check fails. |
| `tests/` | Unit tests that mock subprocess. No device required. |
| `logs/` | Failure logcat dumps. The dumps are not committed. |
| `Android-Python-Automation-Assignment.pdf` | The scanned assignment. |

## Run the skeleton

```bash
python3 main.py
```

## Device used while building

The local emulator AVD is `Pixel_10_Pro` (Android API 37, arm64, with Play Store).
