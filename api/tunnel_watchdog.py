"""Keeps the preview link alive. Run every 5 minutes by a systemd timer.

    python -m api.tunnel_watchdog            # one check (QUOTE_YARD_TUNNEL_EMAIL gets new links)
    python -m api.tunnel_watchdog --print    # say what it sees, change nothing

A Cloudflare quick tunnel can keep running while its link has died ("Tunnel not
found"). After 3 failed checks in a row, while the internet itself works, the
tunnel is restarted, at most once every 30 minutes. Whenever a working link is
new (after a restart of the tunnel or the whole server), it is emailed.
"""

import argparse
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from api.mailer import get_mailer
from api.status_report import SERVICES, link_works, preview_link

UNIT = SERVICES["Preview link"]
FAILURES_BEFORE_RESTART = 3
RESTART_GAP = 30 * 60  # seconds
INTERNET_CHECK = "https://www.cloudflare.com/cdn-cgi/trace"
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "quote-yard" / "tunnel-watchdog.json"


def load(path: Path = STATE) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save(state: dict, path: Path = STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(path)


def internet_works() -> bool:
    request = urllib.request.Request(INTERNET_CHECK, headers={"User-Agent": "quote-yard-watchdog"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def restart_tunnel() -> None:
    subprocess.run(["systemctl", "--user", "restart", UNIT], timeout=60, check=False)


def new_link_email(link: str) -> tuple[str, str]:
    return ("Quote Yard: new preview link",
            f"The Quote Yard preview link changed. The new one is:\n\n  {link}\n\n"
            "The old link no longer works. Share this one with testers.\n\n"
            "Sent by the Quote Yard server. This stops once the site has its own domain.\n")


def check(state: dict, *, link: str | None, works, online, restart, send, now: float) -> tuple[dict, str]:
    """One check. Returns the new state and what happened, in words."""
    state = dict(state)
    if link and works(link):
        state["failures"] = 0
        if link == state.get("emailed"):
            return state, f"ok: {link}"
        if "emailed" not in state:  # first run: remember the link without an email
            state["emailed"] = link
            return state, f"ok, remembered: {link}"
        try:
            send(*new_link_email(link))
        except Exception as exc:  # try again on the next check
            return state, f"ok, but emailing the new link failed: {exc}"
        state["emailed"] = link
        return state, f"ok, emailed new link: {link}"

    if not online():
        return state, "link not working, but the internet is down: waiting"
    state["failures"] = state.get("failures", 0) + 1
    if state["failures"] < FAILURES_BEFORE_RESTART:
        return state, f"link not working ({state['failures']} of {FAILURES_BEFORE_RESTART})"
    if now - state.get("restarted_at", 0) < RESTART_GAP:
        return state, "link not working; restarted recently, waiting"
    restart()
    state["failures"] = 0
    state["restarted_at"] = now
    return state, "link not working: tunnel restarted"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--print", action="store_true", help="only report, change nothing")
    args = parser.parse_args()
    link = preview_link()
    if args.print:
        print(f"link: {link}\nworks: {link_works(link)}\nstate: {load()}")
        return
    to = os.environ.get("QUOTE_YARD_TUNNEL_EMAIL")
    if not to:
        raise SystemExit("Set QUOTE_YARD_TUNNEL_EMAIL to run the watchdog.")
    state, said = check(load(), link=link, works=link_works, online=internet_works,
                        restart=restart_tunnel, send=lambda subject, body: get_mailer().send(to, subject, body),
                        now=time.time())
    save(state)
    print(said)


if __name__ == "__main__":
    main()
