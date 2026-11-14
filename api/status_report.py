"""Twice-daily status email for the owner: activity counts and server health.

    python -m api.status_report            # send it (QUOTE_YARD_REPORT_EMAIL)
    python -m api.status_report --print    # print it here instead

Counts only: no names or email addresses go in the report. It only reads.
"""

import argparse
import glob
import json
import os
import re
import socket
import subprocess
import time as clock
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import text

from api.mailer import get_mailer

IST = ZoneInfo("Asia/Kolkata")
SLOTS = (time(7, 0), time(14, 0))  # keep in step with deploy/install-report.sh
PIPELINE = "quote-yard-pipeline.service"
BACKUP = "quote-yard-backup.service"
SERVICES = {"Website": "quote-yard-api.service", "Site link": "quote-yard-tunnel.service"}
FAILED_LOGIN = re.compile(r'"POST /api/v1/auth/login HTTP/[\d.]+" 401')
NORMALIZATION_REPORT = Path(__file__).resolve().parent.parent / "reports" / "normalization_report.json"


# ---------------------------------------------------------------- the period
def period(now: datetime) -> tuple[datetime, datetime]:
    """From the slot before the latest one up to now: 14:00 to 07:00, then 07:00 to 14:00."""
    slots = sorted(
        datetime.combine(now.date() + timedelta(days=d), t, IST)
        for d in (-2, -1, 0) for t in SLOTS
    )
    past = [s for s in slots if s <= now]
    return past[-2], now


# ---------------------------------------------------------------- reading
def run(*command: str) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def first(pattern: str) -> str | None:
    found = sorted(glob.glob(pattern))
    return found[0] if found else None


# Only systemd's own lines: the job's output could say "Finished" too.
JOB_DONE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d)\S*\s\S+\ssystemd\[\d+\]: (Finished |\S+: Failed with result|Failed to start )")


def last_run_in_logs(unit: str) -> dict[str, str]:
    """After a restart systemd forgets the last run, but the logs keep it."""
    log = run("journalctl", "--user", "-u", unit, "--no-pager", "-o", "short-iso", "-n", "400")
    for line in reversed(log.splitlines()):
        found = JOB_DONE.match(line)
        if found:
            when, what = found.groups()
            return {"LoggedFinish": when.replace("T", " "),
                    "LoggedResult": "success" if what == "Finished " else "failed"}
    return {}


def unit_info(unit: str) -> dict[str, str]:
    out = run("systemctl", "--user", "show", unit,
              "-p", "ActiveState", "-p", "Result", "-p", "ExecMainExitTimestamp")
    info = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    if not info.get("ExecMainExitTimestamp"):
        info.update(last_run_in_logs(unit))
    return info


def link_works(link: str | None, timeout: float = 15) -> bool:
    """Opens the public link's health check the way a visitor would."""
    if not link:
        return False
    request = urllib.request.Request(f"{link}/api/v1/health", headers={"User-Agent": "quote-yard-status"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def boot_time() -> datetime | None:
    for line in (read("/proc/stat") or "").splitlines():
        if line.startswith("btime "):
            return datetime.fromtimestamp(int(line.split()[1]), IST)
    return None


def last_shutdown_clean() -> bool | None:
    """Did the boot before this one end with a proper shutdown? None: no record."""
    log = run("journalctl", "-b", "-1", "-n", "40", "--no-pager", "-o", "cat")
    if not log:
        return None
    return any(mark in log for mark in ("shutdown.target", "System Reboot", "System Power Off"))


def activity(start: datetime, end: datetime) -> dict[str, int]:
    from db.session import get_engine

    with get_engine().connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        q = lambda sql: c.execute(text(sql), {"s": start, "e": end}).one()
        signups, confirmed = q("SELECT count(*), count(email_verified_at) FROM users "
                               "WHERE created_at >= :s AND created_at < :e")
        logins, people = q("SELECT count(*), count(DISTINCT user_id) FROM user_sessions "
                           "WHERE created_at >= :s AND created_at < :e")
        total, total_confirmed = q("SELECT count(*), count(email_verified_at) FROM users")
        saved, = q("SELECT count(*) FROM saved_products")
        alerts, = q("SELECT count(*) FROM price_alerts")
    return {"signups": signups, "signups_confirmed": confirmed, "logins": logins,
            "login_people": people, "users": total, "users_confirmed": total_confirmed,
            "saved": saved, "alerts": alerts}


def normalization() -> dict:
    """From the latest price update: products skipped for a new store category."""
    try:
        with open(NORMALIZATION_REPORT) as f:
            report = json.load(f)
    except (OSError, ValueError):
        return {}
    return {"skipped": report.get("unmapped_combinations", []),
            "held": report.get("held_back_shops", [])}


def failed_logins(start: datetime) -> int:
    log = run("journalctl", "--user", "-u", SERVICES["Website"], "--no-pager", "-o", "cat",
              "--since", start.strftime("%Y-%m-%d %H:%M:%S"))
    return len(FAILED_LOGIN.findall(log))


def site_link() -> str | None:
    """The public address (QUOTE_YARD_SITE_URL), e.g. https://quoteyard.in."""
    return os.environ.get("QUOTE_YARD_SITE_URL", "").strip().rstrip("/") or None


def cpu_temp(settle: float = 8) -> int | None:
    """Read after a short wait: starting this script warms the CPU for a few seconds."""
    clock.sleep(settle)
    for hwmon in glob.glob("/sys/class/hwmon/hwmon*"):
        if read(f"{hwmon}/name") == "coretemp":
            value = read(f"{hwmon}/temp1_input")
            return int(value) // 1000 if value else None
    return None


def battery() -> tuple[str | None, str | None]:
    base = first("/sys/class/power_supply/BAT*")
    if base is None:
        return None, None
    return read(f"{base}/capacity"), read(f"{base}/status")


def screen() -> str:
    dpms = read(first("/sys/class/drm/card*-eDP-*/dpms") or "")
    lid = read(first("/proc/acpi/button/lid/*/state") or "") or ""
    state = {"On": "on", "Off": "off"}.get(dpms or "", "unknown")
    lid_state = "closed" if "closed" in lid else "open" if "open" in lid else None
    return f"{state} (lid {lid_state})" if lid_state else state


def disk_used() -> int | None:
    try:
        st = os.statvfs("/")
    except OSError:
        return None
    used = st.f_blocks - st.f_bfree
    usable = used + st.f_bavail  # as df counts it: space kept back for root is left out
    return round(100 * used / usable) if usable else None


def uptime() -> str:
    value = read("/proc/uptime")
    if not value:
        return "unknown"
    minutes = int(float(value.split()[0]) // 60)
    days, minutes = divmod(minutes, 24 * 60)
    hours, minutes = divmod(minutes, 60)
    return f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"


def wifi() -> str | None:
    for line in run("nmcli", "-t", "-f", "IN-USE,SIGNAL,SSID", "dev", "wifi").splitlines():
        if line.startswith("*:"):
            _, signal, ssid = line.split(":", 2)
            return f"{ssid} ({signal}% signal)"
    return None


# ---------------------------------------------------------------- the email
@dataclass
class Report:
    start: datetime
    end: datetime
    host: str
    activity: dict[str, int]
    failed_logins: int
    pipeline: dict[str, str]
    backup: dict[str, str]
    services: dict[str, str]
    site: str | None
    uptime: str
    cpu_temp: int | None
    screen: str
    battery: tuple[str | None, str | None]
    disk_used: int | None
    wifi: str | None
    normalization: dict = field(default_factory=dict)
    booted: datetime | None = None
    clean_shutdown: bool | None = None


def outcome(info: dict[str, str]) -> str:
    if info.get("ActiveState") in ("active", "activating"):
        return "running now"
    when = info.get("ExecMainExitTimestamp", "")
    if when:
        ok = info.get("Result") == "success"
        when = f" (finished {when.split(' ', 1)[-1][:16]})"
    elif info.get("LoggedFinish"):
        ok = info.get("LoggedResult") == "success"
        when = f" (finished {info['LoggedFinish']}, before the server restarted)"
    else:
        return "no record of it running"
    return ("success" if ok else "FAILED") + when


def compose(r: Report) -> tuple[str, str]:
    a = r.activity
    span = f"{r.start:%d %b %H:%M} to {r.end:%d %b %H:%M} IST"
    problems = [n for n, s in r.services.items() if s != "active"]
    if "FAILED" in outcome(r.pipeline) or "FAILED" in outcome(r.backup):
        problems.append("nightly jobs")
    held = r.normalization.get("held", [])
    skipped = r.normalization.get("skipped", [])
    problems += [f"{h['shop']} prices held back" for h in held]
    notes = ["new store categories to add"] if skipped else []
    restarted = r.booted is not None and r.booted >= r.start
    if restarted and r.clean_shutdown is False:
        notes.append("the server restarted unexpectedly (power cut or crash?)")
    subject = (f"Quote Yard report {r.end:%d %b %H:%M}: "
               f"{a['signups']} new sign-up{'s' * (a['signups'] != 1)}, {a['logins']} login{'s' * (a['logins'] != 1)}"
               + (" - CHECK THE SERVER" if problems else ""))
    jobs_extra = []
    if skipped:
        jobs_extra.append(f"  Skipped products    {sum(c['count'] for c in skipped)}, in new store categories:")
        jobs_extra += [f"    {c['shop']} / {c['category']} / {c['subcategory']} ({c['count']})"
                       for c in skipped]
    for h in held:
        jobs_extra.append(f"  Held back           {h['shop']}: {h['skipped']} of {h['products']} products "
                          "in unknown categories, kept yesterday's prices")
    level, status = r.battery
    lines = [
        f"Quote Yard report, {span}",
        "",
        "PEOPLE (counts only)",
        f"  New sign-ups        {a['signups']}  ({a['signups_confirmed']} confirmed their email)",
        f"  Logins              {a['logins']}  (by {a['login_people']} people)",
        f"  Wrong passwords     {r.failed_logins}",
        f"  All users           {a['users']}  ({a['users_confirmed']} confirmed)",
        f"  Saved products      {a['saved']}",
        f"  Price alerts        {a['alerts']}",
        "",
        "NIGHTLY JOBS",
        f"  Price update        {outcome(r.pipeline)}",
        f"  Backup              {outcome(r.backup)}",
        *jobs_extra,
        "",
        "SERVER",
        *[f"  {name:<20}{'running' if s == 'active' else s.upper()}" for name, s in r.services.items()],
        f"  Site address        {r.site or 'not set'}",
        f"  Up for              {r.uptime}",
        *([f"  Restarted           {r.booted:%d %b %H:%M}"
           + (", planned" if r.clean_shutdown else ", unexpected" if r.clean_shutdown is False else "")
           ] if restarted else []),
        f"  CPU temperature     {f'{r.cpu_temp} C' if r.cpu_temp is not None else 'unknown'}",
        f"  Screen              {r.screen}",
        f"  Battery             {f'{level}% ({status.lower()})' if level else 'unknown'}",
        f"  Disk used           {f'{r.disk_used}%' if r.disk_used is not None else 'unknown'}",
        f"  Wi-Fi               {r.wifi or 'not on Wi-Fi'}",
        "",
        "Sent by the Quote Yard server at 07:00 and 14:00 every day.",
    ]
    if problems or notes:
        lines[0:0] = [f"Needs a look: {', '.join(problems + notes)}.", ""]
    return subject, "\n".join(lines) + "\n"


def services(link: str | None) -> dict[str, str]:
    """A running tunnel can still lead nowhere, so the site address itself is opened."""
    state = {name: run("systemctl", "--user", "is-active", unit) or "unknown"
             for name, unit in SERVICES.items()}
    if state["Site link"] == "active" and not link_works(link):
        state["Site link"] = "not working"
    return state


def gather(now: datetime) -> Report:
    start, end = period(now)
    link = site_link()
    return Report(
        start=start, end=end, host=socket.gethostname(),
        activity=activity(start, end), failed_logins=failed_logins(start),
        pipeline=unit_info(PIPELINE), backup=unit_info(BACKUP),
        services=services(link),
        site=link, uptime=uptime(), cpu_temp=cpu_temp(), screen=screen(),
        battery=battery(), disk_used=disk_used(), wifi=wifi(), normalization=normalization(),
        booted=boot_time(), clean_shutdown=last_shutdown_clean(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--print", action="store_true", help="print instead of sending")
    args = parser.parse_args()
    subject, body = compose(gather(datetime.now(IST)))
    if args.print:
        print(f"Subject: {subject}\n\n{body}")
        return
    to = os.environ.get("QUOTE_YARD_REPORT_EMAIL")
    if not to:
        raise SystemExit("Set QUOTE_YARD_REPORT_EMAIL to send the report.")
    get_mailer().send(to, subject, body)
    print(f"Sent {subject!r}")


if __name__ == "__main__":
    main()
