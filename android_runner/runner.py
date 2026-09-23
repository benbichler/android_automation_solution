from android_runner.adb import AdbError, run_adb


class DeviceError(Exception):
    pass


def select_device(config): # selects a device from the list
    code, out, err = run_adb(["devices"])
    if code != 0:
        detail = err.strip() or out.strip() or f"adb devices exited {code}"
        raise DeviceError(detail)

    devices = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices") or line.startswith("*"):
            continue
        serial, rest = line.split(None, 1)
        devices.append((serial, rest.split()[0]))

    if config.device_id:
        for serial, state in devices:
            if serial != config.device_id:
                continue
            if state != "device":
                raise DeviceError(f"{serial} is {state}.")
            return serial
        raise DeviceError(f"No device with id {config.device_id} is connected.")

    ready = [serial for serial, state in devices if state == "device"]
    if not devices:
        raise DeviceError("No Android device or emulator is connected.")
    if not ready:
        described = ", ".join(f"{serial} is {state}" for serial, state in devices)
        raise DeviceError(f"No usable device is connected. {described}.")
    if len(ready) > 1:
        names = ", ".join(ready)
        raise DeviceError(
            f"More than one device is connected ({names}). Set device_id in config.json."
        )
    return ready[0]


def collect_device_info(serial): # running all getprops and battery dump
    code, out, err = run_adb(["-s", serial, "shell", "getprop", "ro.build.version.release"])
    android_version = out.strip() if code == 0 and out.strip() else None

    code, out, err = run_adb(["-s", serial, "shell", "getprop", "ro.product.model"])
    model = out.strip() if code == 0 and out.strip() else None

    code, out, err = run_adb(["-s", serial, "shell", "getprop", "ro.product.manufacturer"])
    manufacturer = out.strip() if code == 0 and out.strip() else None

    code, out, err = run_adb(["-s", serial, "shell", "dumpsys", "battery"])
    battery = None
    if code == 0:
        for line in out.splitlines():
            text = line.strip()
            if text.startswith("level:"):
                try:
                    battery = int(text.split(":", 1)[1].strip())
                except ValueError:
                    battery = None
                break

    return {
        "serial": serial,
        "android_version": android_version,
        "model": model,
        "manufacturer": manufacturer,
        "battery": battery,
    }


def run_checks(serial, config, info):
    checks = [
        _safe("Device is reachable", check_reachable, serial),
        check_version(info, config),
        check_battery(info, config),
    ]

    install = _safe("Application installation", check_installed, serial, config)
    checks.append(install)

    if install["status"] == "PASS":
        checks.append(_safe("Launch application", check_launch, serial, config))
    else:
        checks.append(_result(
            "Launch application", "SKIP",
            "Install check did not pass, so launch was not attempted.",
        ))
    return checks


def check_reachable(serial):
    code, out, err = run_adb(["-s", serial, "shell", "echo", "hello"])
    out, err = out.strip(), err.strip()
    if code == 0 and out == "hello":
        return _result("Device is reachable", "PASS", 'Command returned "hello".')
    return _result("Device is reachable", "FAIL", err or out or f"exit code {code}")


def check_version(info, config):
    name = "Android version"
    raw = info.get("android_version")
    if not raw:
        return _result(name, "FAIL", "Could not read the Android version.")
    try:
        major = int(str(raw).split(".")[0])
    except ValueError:
        return _result(name, "FAIL", f"Could not parse Android version {raw}.")

    minimum = config.minimum_android_version
    if major >= minimum:
        return _result(name, "PASS", f"Installed major version {major} is greater than or equal to {minimum}.")
    return _result(name, "FAIL", f"Installed major version {major} is below {minimum}.")


def check_battery(info, config):
    name = "Battery level"
    level = info.get("battery")
    minimum = config.minimum_battery
    if level is None:
        return _result(name, "FAIL", "Could not read the battery level.")
    if level > minimum:
        return _result(name, "PASS", f"Battery is {level}%, which is above {minimum}%.")
    return _result(name, "FAIL", f"Battery is {level}%, and the threshold is strictly above {minimum}%.")


def check_installed(serial, config):
    name = "Application installation"
    code, out, err = run_adb(["-s", serial, "shell", "pm", "path", config.package_name])
    for line in out.splitlines():
        if line.strip().startswith("package:"):
            return _result(name, "PASS", f"Package path: {line.strip()}")
    return _result(name, "FAIL", f"Package {config.package_name} is not installed.")


def check_launch(serial, config):
    name = "Launch application"
    code, out, err = run_adb([
        "-s", serial, "shell", "am", "start",
        "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.LAUNCHER",
        "-p", config.package_name,
    ])
    out, err = out.strip(), err.strip()
    # am start can exit 0 and still print "Error: Activity not started".
    if code == 0 and "Starting:" in out and "Error" not in out and "Error" not in err:
        return _result(name, "PASS", "Activity manager started the launcher activity.")
    return _result(name, "FAIL", out or err or f"exit code {code}")


def _safe(name, check, *args):
    """Run a check that talks to adb. A timeout or missing adb fails only this check."""
    try:
        return check(*args)
    except AdbError as exc:
        return _result(name, "FAIL", str(exc))


def _result(name, status, detail):
    return {"name": name, "status": status, "detail": detail}
