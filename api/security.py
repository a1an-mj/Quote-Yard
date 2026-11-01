"""Password, one-time code and session token primitives."""

import hashlib
import os
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError

_hasher = PasswordHasher()
# Verified against when an account does not exist, so that case takes as long.
_DUMMY_HASH = _hasher.hash("quote-yard-dummy-value")


def hash_secret(value: str) -> str:
    """Argon2id hash for a password or a one-time code."""
    return _hasher.hash(value)


def verify_secret(stored_hash: str | None, value: str) -> bool:
    try:
        ok = _hasher.verify(stored_hash or _DUMMY_HASH, value)
    except (Argon2Error, InvalidHashError):
        return False
    return ok and stored_hash is not None


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Session tokens are long and random, so a fast hash is enough."""
    return hashlib.sha256(token.encode()).hexdigest()


def is_admin_email(email: str) -> bool:
    """Admins are the customer accounts listed in QUOTE_YARD_ADMIN_EMAILS (comma separated)."""
    raw = os.environ.get("QUOTE_YARD_ADMIN_EMAILS", "")
    return email.lower() in {e.strip().lower() for e in raw.split(",") if e.strip()}
