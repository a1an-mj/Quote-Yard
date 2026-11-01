import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.mailer import send_safely
from api.notify_failure import notify, recipient


class FakeMailer:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, to, subject, body):
        if self.fail:
            raise OSError("smtp down")
        self.sent.append((to, subject, body))


def test_report_names_the_job_and_includes_the_log():
    mailer = FakeMailer()
    notify("quote-yard-pipeline.service", mailer, "scrape myg FAILED", "me@example.com", "vivobook")
    to, subject, body = mailer.sent[0]
    assert to == "me@example.com"
    assert subject == "Quote Yard: the nightly update failed on vivobook"
    assert "scrape myg FAILED" in body
    assert "journalctl --user -u quote-yard-pipeline.service" in body


def test_unknown_unit_still_reports():
    mailer = FakeMailer()
    notify("something-else.service", mailer, "x", "me@example.com", "h")
    assert "something-else.service" in mailer.sent[0][1]


def test_recipient_prefers_the_alert_address(monkeypatch):
    monkeypatch.setenv("QUOTE_YARD_SMTP_USER", "sender@example.com")
    monkeypatch.delenv("QUOTE_YARD_SMTP_FROM", raising=False)
    monkeypatch.delenv("QUOTE_YARD_ALERT_EMAIL", raising=False)
    assert recipient() == "sender@example.com"
    monkeypatch.setenv("QUOTE_YARD_ALERT_EMAIL", "me@example.com")
    assert recipient() == "me@example.com"


def test_sent_mail_logged_by_subject_only(caplog):
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        send_safely(FakeMailer(), "anu@example.com", "Verify your email", "code is 123456")
    assert "Sent 'Verify your email'" in caplog.text
    assert "anu@example.com" not in caplog.text and "123456" not in caplog.text


def test_failed_mail_logged_without_raising(caplog):
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        send_safely(FakeMailer(fail=True), "anu@example.com", "Verify", "code is 123456")
    assert "Could not send 'Verify'" in caplog.text and "Sent 'Verify'" not in caplog.text
    assert "123456" not in caplog.text
