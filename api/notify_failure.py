"""Email a failure report for a systemd unit. Run by the units' OnFailure hook.

Usage: python -m api.notify_failure quote-yard-pipeline.service
"""

import os
import socket
import subprocess
import sys

from api.mailer import get_mailer

LOG_LINES = 40
PLAIN_NAMES = {
    "quote-yard-pipeline.service": "the nightly update",
    "quote-yard-backup.service": "the backup",
    "quote-yard-api.service": "the website",
}


def recent_log(unit: str, lines: int = LOG_LINES) -> str:
    try:
        return subprocess.run(
            ["journalctl", "--user", "-u", unit, "-n", str(lines), "--no-pager", "-o", "cat"],
            capture_output=True, text=True, timeout=20,
        ).stdout.strip() or "(no log output)"
    except (OSError, subprocess.SubprocessError) as exc:
        return f"(could not read the log: {exc})"


def recipient() -> str | None:
    return (os.environ.get("QUOTE_YARD_ALERT_EMAIL")
            or os.environ.get("QUOTE_YARD_SMTP_FROM")
            or os.environ.get("QUOTE_YARD_SMTP_USER"))


def notify(unit: str, mailer, log_text: str, to: str | None, host: str) -> None:
    name = PLAIN_NAMES.get(unit, unit)
    subject = f"Quote Yard: {name} failed on {host}"
    body = (f"{name.capitalize()} ({unit}) failed on {host}.\n\n"
            f"See it there with: journalctl --user -u {unit} -e\n\n"
            f"Last lines of its log:\n\n{log_text}\n")
    mailer.send(to or "console", subject, body)


def main() -> None:
    unit = sys.argv[1]
    notify(unit, get_mailer(), recent_log(unit), recipient(), socket.gethostname())
    print(f"Reported the failure of {unit}")


if __name__ == "__main__":
    main()
