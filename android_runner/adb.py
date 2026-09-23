"""Run adb commands."""


def adb_available() -> bool:
    raise NotImplementedError


def run_adb(args, timeout=15):
    raise NotImplementedError
