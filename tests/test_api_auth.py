import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.auth import CODE_MAX_ATTEMPTS, CODE_MAX_PER_HOUR, SESSION_COOKIE
from api.deps import get_session, get_write_session
from api.mailer import get_mailer
from api.main import app
from api.routes import auth as auth_routes
from db.models import Base, EmailCode, User, UserSession
from db.session import get_engine

PREFIX = "/api/v1"
HEADERS = {"X-Quote-Yard": "1"}
EMAIL = "anu@example.com"
PASSWORD = "correct horse"


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))

    def last_code(self):
        return re.search(r"\b(\d{6})\b", self.sent[-1][2]).group(1)


@pytest.fixture(scope="module")
def engine():
    eng = get_engine()
    try:
        with eng.connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL not reachable")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def ctx(engine):
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    mailer = FakeMailer()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_write_session] = lambda: session
    app.dependency_overrides[get_mailer] = lambda: mailer
    yield TestClient(app), session, mailer
    app.dependency_overrides.clear()
    session.close()
    trans.rollback()
    conn.close()


def post(client, path, **body):
    return client.post(f"{PREFIX}/auth/{path}", json=body, headers=HEADERS)


def me(client):
    return client.get(f"{PREFIX}/auth/me")


def expire_cooldown(session):
    """Move code timestamps back past the resend cooldown."""
    for code in session.scalars(select(EmailCode)):
        code.created_at -= timedelta(minutes=2)
    session.flush()


def signed_up(client, mailer, email=EMAIL, password=PASSWORD):
    assert post(client, "register", email=email, password=password).status_code == 202
    assert post(client, "verify-email", email=email, code=mailer.last_code()).status_code == 200


# ---- sign-up ------------------------------------------------------------------

def test_register_stores_a_hash_and_emails_a_code(ctx):
    client, s, mailer = ctx
    r = post(client, "register", email=" Anu@Example.com ", password=PASSWORD)
    assert r.status_code == 202
    user = s.scalar(select(User).where(User.email == EMAIL))
    assert user.email_verified_at is None
    assert PASSWORD not in user.password_hash and user.password_hash.startswith("$argon2id$")
    code = s.scalar(select(EmailCode).where(EmailCode.user_id == user.id))
    assert mailer.sent[0][0] == EMAIL and mailer.last_code() not in code.code_hash


def test_verify_logs_in(ctx):
    client, s, mailer = ctx
    signed_up(client, mailer)
    assert client.cookies.get(SESSION_COOKIE)
    assert me(client).json()["email"] == EMAIL
    assert s.scalar(select(User)).email_verified_at is not None


def test_session_cookie_is_http_only_and_only_its_hash_is_stored(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    r = post(client, "verify-email", email=EMAIL, code=mailer.last_code())
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    token = client.cookies.get(SESSION_COOKIE)
    assert s.scalar(select(UserSession)).token_hash != token


@pytest.mark.parametrize("password", ["short12", "x" * 129])
def test_password_length_enforced(ctx, password):
    client, _, _ = ctx
    assert post(client, "register", email=EMAIL, password=password).status_code == 422


def test_eight_characters_is_enough(ctx):
    client, _, _ = ctx
    assert post(client, "register", email=EMAIL, password="12345678").status_code == 202


@pytest.mark.parametrize("email", ["nope", "a@b", "a b@c.d", "x@" + "y" * 260 + ".com"])
def test_bad_email_rejected(ctx, email):
    client, _, _ = ctx
    assert post(client, "register", email=email, password=PASSWORD).status_code == 422


def test_existing_account_gets_the_same_reply_and_no_email(ctx):
    client, s, mailer = ctx
    signed_up(client, mailer)
    before = s.scalar(select(User)).password_hash
    sent = len(mailer.sent)
    r = post(client, "register", email=EMAIL, password="another password")
    assert r.status_code == 202 and r.json()["message"] == auth_routes.CHECK_EMAIL
    assert len(mailer.sent) == sent and s.scalar(select(User)).password_hash == before


def test_unverified_reregister_takes_the_new_password(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password="first password")
    expire_cooldown(s)
    post(client, "register", email=EMAIL, password="second password")
    post(client, "verify-email", email=EMAIL, code=mailer.last_code())
    client.cookies.clear()
    assert post(client, "login", email=EMAIL, password="first password").status_code == 401
    assert post(client, "login", email=EMAIL, password="second password").status_code == 200


def test_honeypot_creates_nothing(ctx):
    client, s, mailer = ctx
    r = post(client, "register", email=EMAIL, password=PASSWORD, website="http://spam")
    assert r.status_code == 202 and s.scalar(select(User)) is None and not mailer.sent


# ---- codes --------------------------------------------------------------------

def test_wrong_code_rejected_and_counted(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    wrong = "000000" if mailer.last_code() != "000000" else "111111"
    r = post(client, "verify-email", email=EMAIL, code=wrong)
    assert r.status_code == 400 and s.scalar(select(EmailCode)).attempts == 1
    assert s.scalar(select(User)).email_verified_at is None


def test_too_many_wrong_codes_kills_the_code(ctx):
    client, _, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    right = mailer.last_code()
    wrong = "000000" if right != "000000" else "111111"
    for _ in range(CODE_MAX_ATTEMPTS):
        post(client, "verify-email", email=EMAIL, code=wrong)
    assert post(client, "verify-email", email=EMAIL, code=right).status_code == 400


def test_expired_code_rejected(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    s.scalar(select(EmailCode)).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    s.flush()
    assert post(client, "verify-email", email=EMAIL, code=mailer.last_code()).status_code == 400


def test_code_works_only_once(ctx):
    client, _, mailer = ctx
    signed_up(client, mailer)
    assert post(client, "verify-email", email=EMAIL, code=mailer.last_code()).status_code == 400


def test_unknown_email_looks_like_a_wrong_code(ctx):
    client, _, _ = ctx
    r = post(client, "verify-email", email="who@example.com", code="123456")
    assert r.status_code == 400 and r.json()["detail"] == auth_routes.BAD_CODE


def test_resend_cooldown_then_new_code_cancels_old(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    first = mailer.last_code()
    post(client, "resend-code", email=EMAIL)
    assert len(mailer.sent) == 1  # inside the cooldown
    expire_cooldown(s)
    post(client, "resend-code", email=EMAIL)
    assert len(mailer.sent) == 2
    if first != mailer.last_code():
        assert post(client, "verify-email", email=EMAIL, code=first).status_code == 400
    assert post(client, "verify-email", email=EMAIL, code=mailer.last_code()).status_code == 200


def test_hourly_cap_on_codes(ctx):
    client, s, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    for _ in range(CODE_MAX_PER_HOUR + 2):
        for code in s.scalars(select(EmailCode)):
            code.created_at -= timedelta(seconds=61)
        s.flush()
        post(client, "resend-code", email=EMAIL)
    assert len(mailer.sent) == CODE_MAX_PER_HOUR


# ---- login, logout -------------------------------------------------------------

def test_login_logout(ctx):
    client, _, mailer = ctx
    signed_up(client, mailer)
    client.cookies.clear()
    assert me(client).status_code == 401
    assert post(client, "login", email=EMAIL.upper(), password=PASSWORD).status_code == 200
    token = client.cookies.get(SESSION_COOKIE)
    assert me(client).status_code == 200
    assert post(client, "logout").status_code == 204
    client.cookies.set(SESSION_COOKIE, token)  # the old token is dead on the server too
    assert me(client).status_code == 401


def test_wrong_password_and_unknown_email_look_the_same(ctx):
    client, _, mailer = ctx
    signed_up(client, mailer)
    client.cookies.clear()
    a = post(client, "login", email=EMAIL, password="wrong password")
    b = post(client, "login", email="who@example.com", password=PASSWORD)
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_unverified_login_blocked_only_after_right_password(ctx):
    client, _, _ = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    assert post(client, "login", email=EMAIL, password="wrong password").status_code == 401
    r = post(client, "login", email=EMAIL, password=PASSWORD)
    assert r.status_code == 403 and r.json()["detail"] == "email_not_verified"


def test_deactivated_account_cannot_log_in_or_use_a_session(ctx):
    client, s, mailer = ctx
    signed_up(client, mailer)
    s.scalar(select(User)).is_active = False
    s.flush()
    assert me(client).status_code == 401
    assert post(client, "login", email=EMAIL, password=PASSWORD).status_code == 401


def test_expired_session_rejected(ctx):
    client, s, mailer = ctx
    signed_up(client, mailer)
    s.scalar(select(UserSession)).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    s.flush()
    assert me(client).status_code == 401


def test_post_without_app_header_refused(ctx):
    client, s, _ = ctx
    r = client.post(f"{PREFIX}/auth/register", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 403 and s.scalar(select(User)) is None


# ---- forgot password -----------------------------------------------------------

def test_reset_changes_password_and_ends_sessions(ctx):
    client, s, mailer = ctx
    signed_up(client, mailer)
    token = client.cookies.get(SESSION_COOKIE)
    assert post(client, "forgot-password", email=EMAIL).status_code == 202
    assert "Reset" in mailer.sent[-1][1]
    r = post(client, "reset-password", email=EMAIL, code=mailer.last_code(),
             new_password="brand new password")
    assert r.status_code == 200
    client.cookies.set(SESSION_COOKIE, token)
    assert me(client).status_code == 401
    client.cookies.clear()
    assert post(client, "login", email=EMAIL, password=PASSWORD).status_code == 401
    assert post(client, "login", email=EMAIL, password="brand new password").status_code == 200


def test_forgot_for_unknown_or_unverified_sends_nothing(ctx):
    client, _, mailer = ctx
    r = post(client, "forgot-password", email="who@example.com")
    assert r.status_code == 202 and not mailer.sent
    post(client, "register", email=EMAIL, password=PASSWORD)
    sent = len(mailer.sent)
    assert post(client, "forgot-password", email=EMAIL).status_code == 202
    assert len(mailer.sent) == sent


def test_verify_code_cannot_reset_a_password(ctx):
    client, _, mailer = ctx
    post(client, "register", email=EMAIL, password=PASSWORD)
    r = post(client, "reset-password", email=EMAIL, code=mailer.last_code(),
             new_password="brand new password")
    assert r.status_code == 400


def test_reset_rejects_short_password(ctx):
    client, _, _ = ctx
    r = post(client, "reset-password", email=EMAIL, code="123456", new_password="short")
    assert r.status_code == 422


# ---- what needs a login ---------------------------------------------------------

@pytest.mark.parametrize("path", [
    "/listings", "/listings/summary", "/listings/1", "/listings/1/prices",
    "/products", "/products/1", "/products/1/prices", "/compare/1",
    "/product-types", "/brands", "/auth/me",
])
def test_data_routes_need_login(ctx, path):
    client, _, _ = ctx
    assert client.get(PREFIX + path).status_code == 401


def test_public_routes_stay_open_and_login_opens_the_rest(ctx):
    client, _, mailer = ctx
    assert client.get(f"{PREFIX}/retailers").status_code == 200
    assert client.get(f"{PREFIX}/health").status_code == 200
    signed_up(client, mailer)
    assert client.get(f"{PREFIX}/products").status_code == 200


def test_cors_allows_credentials_and_the_app_header(ctx):
    client, _, _ = ctx
    r = client.options(f"{PREFIX}/auth/login", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-quote-yard,content-type"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-credentials"] == "true"


def test_auth_rate_limit(ctx, monkeypatch):
    client, _, _ = ctx
    monkeypatch.setenv("QUOTE_YARD_AUTH_RATE_LIMIT", "2")
    auth_routes._limiters.cache_clear()
    try:
        codes = [post(client, "forgot-password", email=EMAIL).status_code for _ in range(3)]
    finally:
        auth_routes._limiters.cache_clear()
    assert codes == [202, 202, 429]
