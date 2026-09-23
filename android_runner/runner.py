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
    checks = []

    try:
        code, out, err = run_adb(["-s", serial, "shell", "echo", "hello"])
    except AdbError as exc:
        checks.append({
            "name": "Device is reachable",
            "status": "FAIL",
            "detail": str(exc),
        })
    else:
        out, err = out.strip(), err.strip()
        if code == 0 and out == "hello":
            checks.append({
                "name": "Device is reachable",
                "status": "PASS",
                "detail": 'Command returned "hello".',
            })
        else:
            checks.append({
                "name": "Device is reachable",
                "status": "FAIL",
                "detail": err or out or f"exit code {code}",
            })

    raw = info.get("android_version")
    if not raw:
        checks.append({
            "name": "Android version",
            "status": "FAIL",
            "detail": "Could not read the Android version.",
        })
    else:
        try:
            major = int(str(raw).split(".")[0])
        except ValueError:
            checks.append({
                "name": "Android version",
                "status": "FAIL",
                "detail": f"Could not parse Android version {raw}.",
            })
        else:
            minimum = config.minimum_android_version
            if major >= minimum:
                detail = f"Installed major version {major} is greater than or equal to {minimum}."
                status = "PASS"
            else:
                detail = f"Installed major version {major} is below {minimum}."
                status = "FAIL"
            checks.append({"name": "Android version", "status": status, "detail": detail})

    level = info.get("battery")
    minimum = config.minimum_battery
    if level is None:
        checks.append({
            "name": "Battery level",
            "status": "FAIL",
            "detail": "Could not read the battery level.",
        })
    elif level > minimum:
        checks.append({
            "name": "Battery level",
            "status": "PASS",
            "detail": f"Battery is {level}%, which is above {minimum}%.",
        })
    else:
        checks.append({
            "name": "Battery level",
            "status": "FAIL",
            "detail": f"Battery is {level}%, and the threshold is strictly above {minimum}%.",
        })

    package_path = None
    install_error = False
    try:
        code, out, err = run_adb(["-s", serial, "shell", "pm", "path", config.package_name])
    except AdbError as exc:
        install_error = True
        checks.append({
            "name": "Application installation",
            "status": "FAIL",
            "detail": str(exc),
        })
    else:
        for line in out.splitlines():
            if line.strip().startswith("package:"):
                package_path = line.strip()
                break
        if package_path:
            checks.append({
                "name": "Application installation",
                "status": "PASS",
                "detail": f"Package path: {package_path}",
            })
        else:
            checks.append({
                "name": "Application installation",
                "status": "FAIL",
                "detail": f"Package {config.package_name} is not installed.",
            })

    if not package_path:
        if install_error:
            detail = "Install check did not finish, so launch was not attempted."
        else:
            detail = "Package is not installed, so launch was not attempted."
        checks.append({
            "name": "Launch application",
            "status": "SKIP",
            "detail": detail,
        })
        return checks

    try:
        code, out, err = run_adb([
            "-s", serial, "shell", "am", "start",
            "-a", "android.intent.action.MAIN",
            "-c", "android.intent.category.LAUNCHER",
            "-p", config.package_name,
        ])
    except AdbError as exc:
        checks.append({
            "name": "Launch application",
            "status": "FAIL",
            "detail": str(exc),
        })
        return checks

    out, err = out.strip(), err.strip()
    if code == 0 and "Starting:" in out and "Error" not in out and "Error" not in err:
        checks.append({
            "name": "Launch application",
            "status": "PASS",
            "detail": "Activity manager started the launcher activity.",
        })
    else:
        checks.append({
            "name": "Launch application",
            "status": "FAIL",
            "detail": out or err or f"exit code {code}",
        })
    return checks
