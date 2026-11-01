#!/usr/bin/env python3
"""Live server screen for the VivoBook: traffic, nightly update status and logs.

    python3 ~/quote-yard/deploy/monitor.py          # press Ctrl+C to stop
    python3 ~/quote-yard/deploy/monitor.py --once   # print one screen and exit

Standard library only. It only reads: nothing here changes the server.
"""
import argparse
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

PORT = 8000
SERVICE = "quote-yard-api"
PIPELINE = "quote-yard-pipeline"
REFRESH_SECONDS = 2
LOCAL_CLIENTS = {"127.0.0.1", "::1"}

ACCESS_LINE = re.compile(
    r'^(?P<time>\S+) \S+ \S+: INFO:\s+(?P<ip>\S+?):\d+ - "(?P<method>\S+) (?P<path>\S+) [^"]*" (?P<status>\d{3})'
)
LOG_PREFIX = re.compile(r"^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)\S* \S+ \S+: (?:INFO:\s+)?")


def run(*command):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def parse_connections(ss_output):
    """Client addresses of established connections, one entry per connection."""
    clients = []
    for line in ss_output.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            address = parts[3].rsplit(":", 1)[0].strip("[]")
            clients.append(address.removeprefix("::ffff:"))
    return clients


def parse_access_line(line):
    found = ACCESS_LINE.match(line)
    if not found:
        return None
    return {
        "time": datetime.fromisoformat(found["time"]),
        "ip": found["ip"].removeprefix("::ffff:"),
        "path": found["path"],
        "status": int(found["status"]),
    }


def summarise(lines, now):
    """Traffic numbers from log lines. The server's own checks do not count as visitors."""
    minute_ago, five_ago = now - timedelta(minutes=1), now - timedelta(minutes=5)
    requests = errors = 0
    visitors = set()
    for line in lines:
        entry = parse_access_line(line)
        if entry is None or entry["ip"] in LOCAL_CLIENTS:
            continue
        if entry["time"] >= five_ago:
            visitors.add(entry["ip"])
            errors += entry["status"] >= 500
        if entry["time"] >= minute_ago:
            requests += 1
    return {"requests_last_minute": requests, "visitors_last_5_minutes": len(visitors),
            "server_errors_last_5_minutes": errors}


def shorten_log(line):
    return LOG_PREFIX.sub(lambda m: f"{m[1]}  ", line)


def render(width, height):
    now = datetime.now().astimezone()
    site = run("systemctl", "--user", "is-active", f"{SERVICE}.service") or "unknown"
    clients = [c for c in parse_connections(
        run("ss", "-Htn", "state", "established", f"( sport = :{PORT} )")) if c not in LOCAL_CLIENTS]
    logs = run("journalctl", "--user", "-u", SERVICE, "--since", "6 min ago",
               "--no-pager", "-o", "short-iso").splitlines()
    numbers = summarise(logs, now)
    update_state = run("systemctl", "--user", "show", f"{PIPELINE}.service", "-p", "ActiveState", "--value")
    update_result = run("systemctl", "--user", "show", f"{PIPELINE}.service", "-p", "Result", "--value")
    update_finished = run("systemctl", "--user", "show", f"{PIPELINE}.service",
                          "-p", "ExecMainExitTimestamp", "--value")
    next_update = run("systemctl", "--user", "show", f"{PIPELINE}.timer",
                      "-p", "NextElapseUSecRealtime", "--value")
    update = "RUNNING NOW" if update_state == "active" else f"{update_result or 'unknown'}, {update_finished or 'never'}"

    header = [
        f"QUOTE YARD SERVER   {now:%d %b %Y %H:%M:%S}   Ctrl+C to stop",
        "-" * min(width, 72),
        f"Site                  {site.upper()}",
        f"Open connections      {len(clients)}  from {len(set(clients))} device(s)",
        f"Requests, last minute {numbers['requests_last_minute']}",
        f"Visitors, last 5 min  {numbers['visitors_last_5_minutes']}",
        f"Server errors, 5 min  {numbers['server_errors_last_5_minutes']}",
        f"Last nightly update   {update}",
        f"Next nightly update   {next_update or 'not scheduled'}",
        "-" * min(width, 72),
        "Latest log lines",
    ]
    room = max(height - len(header) - 1, 1)
    recent = [shorten_log(line) for line in logs if parse_local_noise(line)][-room:]
    return [line[:width] for line in header + (recent or ["(nothing in the last 6 minutes)"])]


def parse_local_noise(line):
    """Hide the health checks made by the server itself; keep everything else."""
    entry = parse_access_line(line)
    return not (entry and entry["ip"] in LOCAL_CLIENTS and entry["path"].endswith("/health"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--once", action="store_true", help="print one screen and exit")
    args = parser.parse_args()

    if args.once:
        size = shutil.get_terminal_size()
        print("\n".join(render(size.columns, size.lines)))
        return
    sys.stdout.write("\033[?25l")  # hide the cursor
    try:
        while True:
            size = shutil.get_terminal_size()
            screen = "\033[K\n".join(render(size.columns, size.lines))
            sys.stdout.write(f"\033[H{screen}\033[J")
            sys.stdout.flush()
            time.sleep(REFRESH_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\n")


if __name__ == "__main__":
    main()
