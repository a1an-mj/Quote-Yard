from fastapi.testclient import TestClient

from api.mailer import get_mailer
from api.main import app
from api.routes import feedback as fb

URL = "/api/v1/public/feedback"
HEADERS = {"X-Quote-Yard": "1"}


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))


def client(monkeypatch, limit=True):
    mailer = FakeMailer()
    app.dependency_overrides[get_mailer] = lambda: mailer
    fb._limiter.cache_clear()
    if not limit:
        monkeypatch.setenv("QUOTE_YARD_RATE_LIMIT", "0")
    else:
        monkeypatch.delenv("QUOTE_YARD_RATE_LIMIT", raising=False)
    monkeypatch.delenv("QUOTE_YARD_FEEDBACK_EMAIL", raising=False)
    return TestClient(app), mailer


def teardown_function():
    app.dependency_overrides.clear()
    fb._limiter.cache_clear()


def test_feedback_is_emailed_to_the_team(monkeypatch):
    c, mailer = client(monkeypatch)
    r = c.post(URL, headers=HEADERS, json={"colour": "sunflower", "fatigue": "a-little",
                                            "mistakes": "Typo on the landing page", "name": "Anu"})
    assert r.status_code == 202
    ((to, subject, body),) = mailer.sent
    assert to == "quoteyard.alerts@gmail.com"
    assert subject == "Quote Yard feedback from Anu"
    assert "Sunflower #FFD23F" in body and "A little" in body and "Typo on the landing page" in body


def test_a_rating_alone_is_enough(monkeypatch):
    c, mailer = client(monkeypatch)
    assert c.post(URL, headers=HEADERS, json={"rating": 7}).status_code == 202
    ((_, _, body),) = mailer.sent
    assert "Overall rating:\n7/10" in body


def test_rating_must_be_1_to_10(monkeypatch):
    c, mailer = client(monkeypatch)
    for bad in (0, 11):
        assert c.post(URL, headers=HEADERS, json={"rating": bad, "problems": "x"}).status_code == 422
    assert mailer.sent == []


def test_empty_feedback_is_refused(monkeypatch):
    c, mailer = client(monkeypatch)
    assert c.post(URL, headers=HEADERS, json={"name": "Anu"}).status_code == 422
    assert mailer.sent == []


def test_honeypot_sends_nothing_but_looks_fine(monkeypatch):
    c, mailer = client(monkeypatch)
    r = c.post(URL, headers=HEADERS, json={"problems": "buy pills", "website": "spam.example"})
    assert r.status_code == 202 and mailer.sent == []


def test_needs_the_app_header(monkeypatch):
    c, _ = client(monkeypatch)
    assert c.post(URL, json={"problems": "x"}).status_code in (400, 403)


def test_unknown_colour_and_long_text_refused(monkeypatch):
    c, _ = client(monkeypatch)
    assert c.post(URL, headers=HEADERS, json={"colour": "rainbow"}).status_code == 422
    assert c.post(URL, headers=HEADERS, json={"problems": "x" * 2001}).status_code == 422


def test_five_an_hour_per_visitor(monkeypatch):
    c, mailer = client(monkeypatch)
    codes = [c.post(URL, headers=HEADERS, json={"problems": f"n{i}"}).status_code for i in range(6)]
    assert codes == [202] * 5 + [429] and len(mailer.sent) == 5


def test_address_can_be_changed(monkeypatch):
    c, mailer = client(monkeypatch, limit=False)
    monkeypatch.setenv("QUOTE_YARD_FEEDBACK_EMAIL", "team@example.com")
    c.post(URL, headers=HEADERS, json={"questions": "When is launch?"})
    assert mailer.sent[0][0] == "team@example.com"
