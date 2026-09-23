from android_runner.adb import AdbError
from android_runner.config import ConfigError, load_config
from android_runner.report import save_failure_log, write_report
from android_runner.runner import DeviceError, collect_device_info, run_checks, select_device


def main():
    try:
        config = load_config("config.json")
        serial = select_device(config)
        info = collect_device_info(serial)
        checks = run_checks(serial, config, info)
    except (ConfigError, AdbError, DeviceError) as exc:
        print(exc)
        return 2

    print(f"Device: {info['serial']}")
    print(f"Android version: {info['android_version']}")
    print(f"Model: {info['model']}")
    print(f"Manufacturer: {info['manufacturer']}")
    print(f"Battery: {info['battery']}%")
    print()
    for check in checks:
        if check["status"] == "FAIL":
            check["log"] = save_failure_log(serial, check["name"])
        print(f"{check['status']:4}  {check['name']}: {check['detail']}")

    print()
    overall = write_report(info, checks)
    print(f"Overall: {overall}")
    print("Wrote report.txt")
    if overall == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
