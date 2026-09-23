# Android Python Automation

A command-line tool that uses adb to look at one Android device or emulator, run five checks, and write `report.txt`.

## Setup

Install Android SDK Platform Tools and make sure `adb` is on your `PATH`.

```bash
adb version
```

On a phone: enable Developer options, turn on USB debugging, plug it in, and accept the "Allow USB debugging?" prompt. Until you accept it, `adb devices` shows the phone as `unauthorized`.

An emulator works too. This was built against the `Pixel_10_Pro` virtual device:

```bash
emulator -avd Pixel_10_Pro
adb devices
```

You want a line whose state is `device`. `emulator-5554` is the usual emulator serial.

## Configuration

Edit `config.json`. Do not hard-code these values in Python.

```json
{
  "package_name": "com.android.settings",
  "minimum_android_version": 10,
  "minimum_battery": 20
}
```

`package_name` is the app to look for and launch. `com.android.settings` is the Settings app, which is already on the emulator. `minimum_android_version` is the major Android release, so `10` means Android 10. `minimum_battery` is a percent. The battery check passes only when the level is strictly above that number.

`device_id` is optional. Add it when more than one device is connected:

```json
"device_id": "emulator-5554"
```

## Run

```bash
python3 main.py
```

That loads the config, picks one device, reads the device facts, runs the five checks, and writes `report.txt`. The launch check opens the configured app, so Settings will come to the front on the emulator.

Exit code `0` means the report is an overall pass. Exit code `1` means at least one check failed. Exit code `2` means setup stopped the run before the checks: bad config, adb missing, or no usable device.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The tests fake `adb`. They pass with no phone and no emulator connected.

## What the code does

`main.py` calls the steps in order.

`android_runner/config.py` reads `config.json` first. A bad file raises `ConfigError` and adb is not contacted.

`android_runner/adb.py` runs one adb command and returns the exit code, normal output, and error output. A missing adb, or a command that sits longer than 15 seconds, raises `AdbError`.

`android_runner/runner.py` parses `adb devices` and keeps a device only when its state is `device`. It then reads the version, model, and manufacturer with `getprop`, and the battery percent from `dumpsys battery`. The five checks are reachability (`echo hello`), Android version, battery, whether the package is installed (`pm path`), and launching it (`am start`). If the package is missing, launch is `SKIP`.

`android_runner/report.py` writes `report.txt`. Overall `PASS` means nothing failed. A skip does not fail the run by itself. Each failed check tries `adb logcat -d` and saves the dump under `logs/`. `-d` makes logcat print and exit. If that dump fails, the original check result is kept and the report is still written. Log dumps are not committed.

## Assumptions

The Android version compared with the config is `ro.build.version.release`, the version shown in Settings, not the API level. Only one ready device is required unless `device_id` is set. The launch check trusts the `am start` result. It does not look at the screen.

## With more time

Filter logcat to the app instead of saving the last 200 lines. Repeat the run on a timer. Write a JSON report next to the text file. Add a storage check with `adb shell df /data`.
