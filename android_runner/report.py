from datetime import datetime
from pathlib import Path

from android_runner.adb import AdbError, run_adb


def write_report(info, results, path="report.txt"):
    passed = 0
    failed = 0
    skipped = 0
    lines = [
        "Device information",
        f"  ID: {info.get('serial')}",
        f"  Android version: {info.get('android_version')}",
        f"  Model: {info.get('model')}",
        f"  Manufacturer: {info.get('manufacturer')}",
        f"  Battery: {info.get('battery')}%",
        "",
        "Results",
    ]

    for result in results:
        status = result["status"]
        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        elif status == "SKIP":
            skipped += 1
        lines.append(f"  {result['name']}: {status}")
        lines.append(f"    {result['detail']}")
        if result.get("log"):
            lines.append(f"    Log: {result['log']}")

    overall = "PASS" if failed == 0 else "FAIL"
    lines.extend([
        "",
        "Totals",
        f"  Passed: {passed}",
        f"  Failed: {failed}",
        f"  Skipped: {skipped}",
        f"  All: {passed + failed + skipped}",
        "",
        f"Overall: {overall}",
        "",
    ])
    Path(path).write_text("\n".join(lines))
    return overall


def save_failure_log(serial, test_name, logs_dir="logs"):
    try:
        code, out, err = run_adb(["-s", serial, "logcat", "-d", "-t", "200"])
    except AdbError:
        return None
    if code != 0 and not out:
        return None

    safe_name = test_name.strip().lower().replace(" ", "_")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = Path(logs_dir) / f"{stamp}_{safe_name}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out if out else err)
    return str(path)
