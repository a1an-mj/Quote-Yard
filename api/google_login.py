"""Checks a "Sign in with Google" ID token (a JWT signed by Google).

The browser gets the token from Google's button and posts it to us. We check
Google's signature against Google's published keys, that it was made for our
client ID, that it has not expired, and that Google has confirmed the email.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

import jwt

GOOGLE_KEYS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class GoogleTokenError(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str  # Google's id for the person; stays the same if they change their email
    email: str
    first_name: str
    last_name: str | None


def client_id() -> str | None:
    """QUOTE_YARD_GOOGLE_CLIENT_ID turns Google sign-in on; unset means off."""
    value = os.environ.get("QUOTE_YARD_GOOGLE_CLIENT_ID", "").strip()
    return value or None


@lru_cache
def _keys() -> jwt.PyJWKClient:
    # Caches Google's keys and fetches again when a token names a new one.
    return jwt.PyJWKClient(GOOGLE_KEYS_URL, cache_keys=True, lifespan=6 * 60 * 60)


def _signing_key(token: str):
    return _keys().get_signing_key_from_jwt(token).key


def verify(token: str, audience: str) -> GoogleIdentity:
    try:
        claims = jwt.decode(
            token,
            _signing_key(token),
            algorithms=["RS256"],
            audience=audience,
            issuer=GOOGLE_ISSUERS,
            leeway=60,
            options={"require": ["exp", "iat", "sub", "email"]},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise GoogleTokenError(str(exc)) from exc
    if claims.get("email_verified") is not True:
        raise GoogleTokenError("Google has not confirmed this email")
    email = str(claims["email"]).strip().lower()
    first = " ".join(str(claims.get("given_name") or "").split())[:50]
    last = " ".join(str(claims.get("family_name") or "").split())[:50] or None
    if not first:
        first = " ".join(str(claims.get("name") or "").split())[:50] or email.split("@")[0][:50]
    return GoogleIdentity(sub=str(claims["sub"]), email=email, first_name=first, last_name=last)
