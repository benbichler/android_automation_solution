"""Write report.txt and keep logcat dumps for failed checks."""


def write_report(info, results, path="report.txt"):
    raise NotImplementedError


def save_failure_log(serial, test_name, logs_dir="logs"):
    raise NotImplementedError
