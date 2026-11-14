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
        services={"Website": "active", "Site link": "active"},
        site="https://quoteyard.in", uptime="1d 2h 3m", cpu_temp=41,
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
                                   services={"Website": "failed", "Site link": "active"}))
    assert subject.endswith("CHECK THE SERVER")
    assert body.startswith("Needs a look: Website, nightly jobs.")
    assert "Price update        FAILED" in body


def test_outcome_without_a_run():
    assert outcome({"ActiveState": "inactive"}) == "no record of it running"
    assert outcome({"ActiveState": "activating"}) == "running now"


def test_skipped_categories_are_listed_without_alarming_the_subject():
    skipped = [{"shop": "Pittappillil", "category": "Kitchen Appliances",
                "subcategory": "Appachatty", "count": 1}]
    subject, body = compose(report(normalization={"skipped": skipped, "held": []}))
    assert "CHECK THE SERVER" not in subject
    assert "Needs a look: new store categories to add." in body
    assert "Pittappillil / Kitchen Appliances / Appachatty (1)" in body


def test_a_held_back_store_flags_the_report():
    held = [{"shop": "Oxygen", "skipped": 40, "products": 300}]
    subject, body = compose(report(normalization={"skipped": [], "held": held}))
    assert subject.endswith("CHECK THE SERVER")
    assert "Oxygen: 40 of 300 products in unknown categories" in body


# ---- after a restart, and the site link --------------------------------------

from api import status_report  # noqa: E402

JOURNAL = """\
2026-11-14T02:06:48+05:30 vivobook systemd[1399]: Starting quote-yard-pipeline.service - Quote Yard daily update...
2026-11-14T02:38:10+05:30 vivobook python[79594]: Result: OK
2026-11-14T02:38:10+05:30 vivobook systemd[1399]: Finished quote-yard-pipeline.service - Quote Yard daily update.
2026-11-14T02:38:10+05:30 vivobook systemd[1399]: quote-yard-pipeline.service: Consumed 41min CPU time.
"""


def fake_run(outputs):
    def run(*command):
        for key, value in outputs.items():
            if key in command:
                return value
        return ""
    return run


def test_last_run_is_found_in_the_logs_after_a_restart(monkeypatch):
    monkeypatch.setattr(status_report, "run", fake_run({"show": "ActiveState=inactive\nResult=success\nExecMainExitTimestamp=",
                                                        "journalctl": JOURNAL}))
    info = status_report.unit_info("quote-yard-pipeline.service")
    assert outcome(info) == "success (finished 2026-11-14 02:38, before the server restarted)"


def test_a_failed_run_in_the_logs_is_a_failure(monkeypatch):
    failed = JOURNAL.replace("Finished quote-yard-pipeline.service - Quote Yard daily update.",
                             "quote-yard-pipeline.service: Failed with result 'exit-code'.")
    monkeypatch.setattr(status_report, "run", fake_run({"show": "ActiveState=failed\nResult=exit-code",
                                                        "journalctl": failed}))
    assert outcome(status_report.unit_info("x")).startswith("FAILED (finished 2026-11-14 02:38")


def test_systemd_record_wins_over_the_logs(monkeypatch):
    monkeypatch.setattr(status_report, "run", fake_run({
        "show": "ActiveState=inactive\nResult=success\nExecMainExitTimestamp=Sat 2026-11-14 02:38:10 IST",
        "journalctl": "should not be read"}))
    assert outcome(status_report.unit_info("x")) == "success (finished 2026-11-14 02:38)"


def test_a_running_tunnel_with_a_dead_link_is_a_problem(monkeypatch):
    monkeypatch.setattr(status_report, "run", fake_run({"is-active": "active"}))
    monkeypatch.setattr(status_report, "link_works", lambda link: False)
    state = status_report.services("https://quoteyard.in")
    assert state == {"Website": "active", "Site link": "not working"}
    subject, body = compose(report(services=state))
    assert subject.endswith("CHECK THE SERVER")
    assert "Site link           NOT WORKING" in body


def test_a_working_link_is_running(monkeypatch):
    monkeypatch.setattr(status_report, "run", fake_run({"is-active": "active"}))
    monkeypatch.setattr(status_report, "link_works", lambda link: True)
    assert status_report.services("https://quoteyard.in")["Site link"] == "active"


def test_the_site_link_comes_from_the_site_url(monkeypatch):
    monkeypatch.setenv("QUOTE_YARD_SITE_URL", "https://quoteyard.in/")
    assert status_report.site_link() == "https://quoteyard.in"
    monkeypatch.delenv("QUOTE_YARD_SITE_URL")
    assert status_report.site_link() is None


def test_a_planned_restart_is_shown_without_alarm():
    subject, body = compose(report(booted=at(6, 4, 30), clean_shutdown=True))
    assert "Restarted           06 Nov 04:30, planned" in body
    assert "Needs a look" not in body and "CHECK" not in subject


def test_an_unexpected_restart_is_noted():
    _, body = compose(report(booted=at(6, 4, 30), clean_shutdown=False))
    assert body.startswith("Needs a look: the server restarted unexpectedly (power cut or crash?).")


def test_a_restart_before_the_period_is_not_shown():
    _, body = compose(report(booted=at(4, 22, 0), clean_shutdown=True))
    assert "Restarted" not in body


def test_the_jobs_own_output_is_not_taken_for_a_finish(monkeypatch):
    log = "2026-11-14T02:20:00+05:30 vivobook python[1]: Finished scraping Oxygen\n"
    monkeypatch.setattr(status_report, "run", fake_run({"show": "ActiveState=inactive", "journalctl": log}))
    assert outcome(status_report.unit_info("x")) == "no record of it running"
