"""Pick a device and run the checks."""

from android_runner.adb import run_adb


class DeviceError(Exception):
    pass


def select_device(config):
    code, out, err = run_adb(["devices"])
    if code != 0:
        detail = err.strip() or out.strip() or f"adb devices exited {code}"
        raise DeviceError(detail)

    devices = _parse_devices(out)
    if config.device_id:
        return _match(config.device_id, devices)

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


def _parse_devices(output):
    found = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices") or line.startswith("*"):
            continue
        serial, rest = line.split(None, 1)
        state = rest.split()[0]
        found.append((serial, state))
    return found


def _match(serial, devices):
    for found, state in devices:
        if found != serial:
            continue
        if state != "device":
            raise DeviceError(f"{serial} is {state}.")
        return serial
    raise DeviceError(f"No device with id {serial} is connected.")


def collect_device_info(serial):
    raise NotImplementedError


def run_checks(serial, config, info):
    raise NotImplementedError
