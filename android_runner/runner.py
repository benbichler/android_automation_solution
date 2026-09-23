"""Pick a device and run the checks."""


def select_device(config):
    raise NotImplementedError


def collect_device_info(serial):
    raise NotImplementedError


def run_checks(serial, config, info):
    raise NotImplementedError
