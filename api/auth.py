"""Login sessions, one-time codes and the checks routes depend on."""

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from api.deps import get_session
from api.security import (
    hash_secret,
    hash_token,
    is_admin_email,
    new_code,
    new_session_token,
    verify_secret,
)
from db.models import EmailCode, User, UserSession

SESSION_COOKIE = "qy_session"
SESSION_LIFETIME = timedelta(days=14)
CODE_LIFETIME = timedelta(minutes=10)
CODE_MAX_ATTEMPTS = 5
CODE_RESEND_COOLDOWN = timedelta(seconds=60)
CODE_MAX_PER_HOUR = 5
# Browsers do not let another site add a custom header without a CORS grant,
# so requiring it on state-changing requests stops cross-site form posts.
CSRF_HEADER = "x-quote-yard"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def cookie_secure() -> bool:
    return os.environ.get("QUOTE_YARD_COOKIE_SECURE", "true").lower() != "false"


def require_app_header(request: Request) -> None:
    if request.method not in ("GET", "HEAD", "OPTIONS") and CSRF_HEADER not in request.headers:
        raise HTTPException(status_code=403, detail="missing X-Quote-Yard header")


def require_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    user = None
    if token:
        user = session.scalar(
            select(User)
            .join(UserSession, UserSession.user_id == User.id)
            .where(
                UserSession.token_hash == hash_token(token),
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > _now(),
                User.is_active.is_(True),
                User.email_verified_at.is_not(None),
            )
        )
    if user is None:
        raise HTTPException(status_code=401, detail="not logged in")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not is_admin_email(user.email):
        raise HTTPException(status_code=403, detail="not allowed")
    return user


def start_session(session: Session, user: User) -> str:
    """Create a login; returns the token for the cookie. Only its hash is stored."""
    token = new_session_token()
    session.add(UserSession(user_id=user.id, token_hash=hash_token(token),
                            expires_at=_now() + SESSION_LIFETIME))
    user.last_login_at = _now()
    return token


def revoke_all_sessions(session: Session, user_id: int) -> None:
    session.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


def issue_code(session: Session, user: User, purpose: str) -> str | None:
    """A new code, cancelling earlier ones; None inside the cooldown or hourly cap."""
    now = _now()
    recent = session.execute(
        select(func.count(EmailCode.id), func.max(EmailCode.created_at)).where(
            EmailCode.user_id == user.id,
            EmailCode.purpose == purpose,
            EmailCode.created_at > now - timedelta(hours=1),
        )
    ).one()
    if recent[0] >= CODE_MAX_PER_HOUR or (recent[1] and recent[1] > now - CODE_RESEND_COOLDOWN):
        return None
    session.execute(
        update(EmailCode)
        .where(EmailCode.user_id == user.id, EmailCode.purpose == purpose,
               EmailCode.used_at.is_(None))
        .values(used_at=now)
    )
    code = new_code()
    session.add(EmailCode(user_id=user.id, purpose=purpose, code_hash=hash_secret(code),
                          expires_at=now + CODE_LIFETIME))
    return code


def consume_code(session: Session, user: User | None, purpose: str, code: str) -> bool:
    """Check a code. Commits, so a wrong attempt still counts when the caller rejects."""
    active = None
    if user is not None:
        active = session.scalar(
            select(EmailCode)
            .where(EmailCode.user_id == user.id, EmailCode.purpose == purpose,
                   EmailCode.used_at.is_(None), EmailCode.expires_at > _now(),
                   EmailCode.attempts < CODE_MAX_ATTEMPTS)
            .order_by(EmailCode.id.desc())
            .limit(1)
            .with_for_update()
        )
    ok = verify_secret(active.code_hash if active else None, code)
    if active is not None:
        if ok:
            active.used_at = _now()
        else:
            active.attempts += 1
        session.commit()
    return ok
