import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.tunnel_watchdog import RESTART_GAP, check, load, save

LINK = "https://old-link.trycloudflare.com"
NEW = "https://new-link.trycloudflare.com"


class World:
    def __init__(self, works=True, online=True):
        self.works, self.online = works, online
        self.restarts, self.sent = 0, []

    def step(self, state, link=LINK, now=10_000.0):
        return check(state, link=link, works=lambda _: self.works, online=lambda: self.online,
                     restart=self.restart, send=lambda s, b: self.sent.append((s, b)), now=now)

    def restart(self):
        self.restarts += 1


def test_first_run_remembers_the_link_without_email():
    w = World()
    state, said = w.step({})
    assert state["emailed"] == LINK and w.sent == [] and "remembered" in said


def test_a_new_working_link_is_emailed_once():
    w = World()
    state, _ = w.step({"emailed": LINK}, link=NEW)
    assert len(w.sent) == 1 and NEW in w.sent[0][1]
    state, _ = w.step(state, link=NEW)
    assert len(w.sent) == 1


def test_a_failed_email_is_tried_again():
    w = World()

    def broken(*_):
        raise OSError("smtp down")

    state, said = check({"emailed": LINK}, link=NEW, works=lambda _: True, online=lambda: True,
                        restart=w.restart, send=broken, now=0)
    assert state["emailed"] == LINK and "failed" in said
    state, _ = w.step(state, link=NEW)
    assert state["emailed"] == NEW and len(w.sent) == 1


def test_restarts_after_three_failures_in_a_row():
    w = World(works=False)
    state = {"emailed": LINK}
    for _ in range(2):
        state, _ = w.step(state)
    assert w.restarts == 0
    state, said = w.step(state)
    assert w.restarts == 1 and state["failures"] == 0 and "restarted" in said


def test_one_good_check_resets_the_count():
    w = World(works=False)
    state, _ = w.step({"emailed": LINK})
    state, _ = w.step(state)
    w.works = True
    state, _ = w.step(state)
    assert state["failures"] == 0


def test_no_restart_while_the_internet_is_down():
    w = World(works=False, online=False)
    state = {"emailed": LINK}
    for _ in range(5):
        state, said = w.step(state)
    assert w.restarts == 0 and state.get("failures", 0) == 0 and "internet is down" in said


def test_at_most_one_restart_per_half_hour():
    w = World(works=False)
    state = {"emailed": LINK, "failures": 2}
    state, _ = w.step(state, now=10_000)
    state["failures"] = 2
    state, said = w.step(state, now=10_000 + RESTART_GAP - 60)
    assert w.restarts == 1 and "recently" in said
    state, _ = w.step(state, now=10_000 + RESTART_GAP + 1)
    assert w.restarts == 2


def test_no_link_found_counts_as_not_working():
    w = World()
    state, _ = w.step({"emailed": LINK, "failures": 2}, link=None)
    assert w.restarts == 1


def test_state_survives_a_save_and_load(tmp_path):
    path = tmp_path / "state.json"
    assert load(path) == {}
    save({"emailed": LINK, "failures": 1}, path)
    assert load(path) == {"emailed": LINK, "failures": 1}
