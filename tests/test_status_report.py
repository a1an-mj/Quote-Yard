import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.status_report import IST, Report, compose, outcome, period


def at(day, hour, minute=0):
    return datetime(2026, 11, day, hour, minute, tzinfo=IST)


def test_morning_report_covers_since_yesterday_afternoon():
    assert period(at(6, 7, 0, )) == (at(5, 14), at(6, 7))


def test_afternoon_report_covers_the_morning():
    assert period(at(6, 14, 1)) == (at(6, 7), at(6, 14, 1))


def test_a_late_run_still_starts_at_the_slot_before():
    # The server was off at 07:00 and the timer caught up at 09:30.
    assert period(at(6, 9, 30)) == (at(5, 14), at(6, 9, 30))


def report(**changes):
    base = dict(
        start=at(5, 14), end=at(6, 7), host="vivobook",
        activity={"signups": 2, "signups_confirmed": 1, "logins": 3, "login_people": 2,
                  "users": 20, "users_confirmed": 17, "saved": 3, "alerts": 4},
        failed_logins=1,
        pipeline={"ActiveState": "inactive", "Result": "success",
                  "ExecMainExitTimestamp": "Fri 2026-11-06 02:46:15 IST"},
        backup={"ActiveState": "inactive", "Result": "success",
                "ExecMainExitTimestamp": "Fri 2026-11-06 03:30:02 IST"},
        services={"Website": "active", "Preview link": "active"},
        preview="https://a-b-c.trycloudflare.com", uptime="1d 2h 3m", cpu_temp=41,
        screen="off (lid open)", battery=("100", "Not charging"), disk_used=3,
        wifi="HUAWEI-8aDA (67% signal)",
    )
    base.update(changes)
    return Report(**base)


def test_report_has_counts_and_server_state():
    subject, body = compose(report())
    assert subject == "Quote Yard report 06 Nov 07:00: 2 new sign-ups, 3 logins"
    assert "New sign-ups        2  (1 confirmed their email)" in body
    assert "Logins              3  (by 2 people)" in body
    assert "Price update        success (finished 2026-11-06 02:46)" in body
    assert "CPU temperature     41 C" in body
    assert "Screen              off (lid open)" in body
    assert "Battery             100% (not charging)" in body
    assert "Needs a look" not in body
    assert "@" not in body  # counts only: no email addresses


def test_one_of_each_is_singular():
    a = dict(report().activity, signups=1, logins=1)
    assert compose(report(activity=a))[0].endswith("1 new sign-up, 1 login")


def test_failures_are_flagged_in_the_subject():
    subject, body = compose(report(pipeline={"Result": "exit-code",
                                             "ExecMainExitTimestamp": "Fri 2026-11-06 02:46:15 IST"},
                                   services={"Website": "failed", "Preview link": "active"}))
    assert subject.endswith("CHECK THE SERVER")
    assert body.startswith("Needs a look: Website, nightly jobs.")
    assert "Price update        FAILED" in body


def test_outcome_without_a_run():
    assert outcome({"ActiveState": "inactive"}) == "has not run since the server started"
    assert outcome({"ActiveState": "activating"}) == "running now"
