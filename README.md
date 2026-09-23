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

## Failure behavior

| Situation | What happens |
| --- | --- |
| adb is not installed | Prints that Android Platform Tools must be installed and adb added to PATH. Exit code 2. |
| No device connected | Prints "No Android device or emulator is connected." Exit code 2. |
| Device is unauthorized or offline | Prints the serial and the state, for example `R5CT123 is unauthorized`. Exit code 2. |
| More than one ready device | Lists them and asks for `device_id` in config.json. Exit code 2. |
| Bad config.json | Names the missing or invalid field. No traceback, adb is not contacted. Exit code 2. |
| An adb command fails or times out during a check | Only that check is `FAIL`, with the error as its detail. The other checks still run. |
| Battery level cannot be read | The battery check is `FAIL` with "Could not read the battery level." |
| Package is not installed | Installation is `FAIL`, launch is `SKIP`. |
| logcat fails after a failed check | The check result is kept and the report is still written, without a log path. |

## Tests

The tests use pytest. Install it inside a virtual environment. On macOS this is required, because Homebrew's Python refuses `pip install` into the system Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Then run from the project folder:

```bash
pytest -v
```

In a new terminal, run `source .venv/bin/activate` again first.

The tests replace `adb` with a fake that returns prepared output, so they pass with no phone and no emulator connected.

## Project structure

```
main.py                 runs the steps in order and sets the exit code
config.json             package name and thresholds
android_runner/
    config.py           reads and validates config.json
    adb.py              runs one adb command with a timeout
    runner.py           picks the device, reads its details, runs the checks
    report.py           writes report.txt and saves logcat for failed checks
tests/                  pytest tests, adb is faked
logs/                   logcat dumps from failed checks (not committed)
```

## Design choices

- **All adb calls go through one function, `run_adb`.** The timeout and the "adb is missing" message live in one place, and the tests only need to fake this one function.
- **The config is checked before adb is touched.** A typo in `config.json` is reported in the first second, not after waiting for a device.
- **One failed check does not stop the others.** Each check is its own function. The ones that call adb run through `_safe`, which turns a timeout into a `FAIL` for that check only. Only setup problems (config, adb, device) stop the run.
- **The launch check reads the output of `am start`, not only its exit code.** `am start` can exit with 0 and still print `Error: Activity not started`.
- **Failed checks save the last 200 lines of logcat** (`adb logcat -d -t 200`). The full log can be thousands of lines. If saving it fails, the check result and the report are kept.

## Assumptions

- The Android version is `ro.build.version.release` (for example `14`, as shown in Settings), not the API level.
- One ready device is expected. With more than one, `device_id` must be set.
- The launch check is command-level. It does not look at the screen.

## With more time

- Filter logcat to the app under test instead of saving the last 200 lines.
- Run on every connected device, not only one.
- Write a JSON report next to the text file.
- Add a storage check with `adb shell df /data`.
- Run the tests in CI (GitHub Actions) on every push.
