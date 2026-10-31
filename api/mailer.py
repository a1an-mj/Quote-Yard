"""Outgoing email. QUOTE_YARD_MAIL_BACKEND picks console (default) or smtp.

smtp reads QUOTE_YARD_SMTP_HOST, _PORT (default 587), _USER, _PASSWORD and
_FROM (default: the user). Keep them in the server's environment, never in git.
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from functools import lru_cache

log = logging.getLogger("uvicorn.error")


class ConsoleMailer:
    """Development: prints the message, one-time code included, to the terminal."""

    def send(self, to: str, subject: str, body: str) -> None:
        print(f"\n--- email to {to}: {subject}\n{body}\n---\n", flush=True)


class SmtpMailer:
    def __init__(self, host, port, user, password, sender):
        self.host, self.port, self.user = host, port, user
        self.password, self.sender = password, sender

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(message)


@lru_cache
def get_mailer():
    backend = os.environ.get("QUOTE_YARD_MAIL_BACKEND", "console")
    if backend == "console":
        return ConsoleMailer()
    if backend == "smtp":
        user = os.environ["QUOTE_YARD_SMTP_USER"]
        return SmtpMailer(
            os.environ["QUOTE_YARD_SMTP_HOST"],
            int(os.environ.get("QUOTE_YARD_SMTP_PORT", "587")),
            user,
            os.environ["QUOTE_YARD_SMTP_PASSWORD"],
            os.environ.get("QUOTE_YARD_SMTP_FROM", user),
        )
    raise RuntimeError(f"Unknown QUOTE_YARD_MAIL_BACKEND {backend!r}")


def send_safely(mailer, to: str, subject: str, body: str) -> None:
    """For background tasks: a mail failure is logged, never shown to the requester."""
    try:
        mailer.send(to, subject, body)
    except Exception:
        log.exception("Could not send %r", subject)
