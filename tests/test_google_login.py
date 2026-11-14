"""The Google ID token check, with our own key standing in for Google's."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from api import google_login
from api.google_login import GoogleTokenError, verify

AUD = "test-client.apps.googleusercontent.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def our_key(monkeypatch):
    monkeypatch.setattr(google_login, "_signing_key", lambda token: KEY.public_key())


def token(key=KEY, **changes):
    now = int(time.time())
    claims = {"iss": "https://accounts.google.com", "aud": AUD, "sub": "g-1",
              "email": "Anu@Example.com", "email_verified": True,
              "given_name": "Anu", "family_name": "K", "iat": now, "exp": now + 600}
    claims.update(changes)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256")


def test_a_good_token_gives_the_person():
    person = verify(token(), AUD)
    assert (person.sub, person.email, person.first_name, person.last_name) == ("g-1", "anu@example.com", "Anu", "K")


@pytest.mark.parametrize("changes", [
    {"aud": "someone-else"},
    {"iss": "https://evil.example.com"},
    {"exp": int(time.time()) - 3600},
    {"email_verified": False},
    {"email_verified": None},
    {"email": None},
    {"sub": None},
])
def test_bad_tokens_are_refused(changes):
    with pytest.raises(GoogleTokenError):
        verify(token(**changes), AUD)


def test_a_token_signed_by_another_key_is_refused():
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(GoogleTokenError):
        verify(token(key=other), AUD)


def test_an_unsigned_token_is_refused():
    bad = jwt.encode({"aud": AUD, "sub": "g-1"}, None, algorithm="none")
    with pytest.raises(GoogleTokenError):
        verify(bad, AUD)


def test_name_falls_back_to_full_name_then_email():
    assert verify(token(given_name=None, name="Anu Mary"), AUD).first_name == "Anu Mary"
    assert verify(token(given_name=None, family_name=None), AUD).first_name == "anu"
