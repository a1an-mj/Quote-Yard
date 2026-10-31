import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import AfterValidator, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth import (
    CODE_LIFETIME,
    SESSION_COOKIE,
    SESSION_LIFETIME,
    consume_code,
    cookie_secure,
    issue_code,
    require_app_header,
    require_user,
    revoke_all_sessions,
    start_session,
)
from api.deps import get_write_session
from api.mailer import get_mailer, send_safely
from api.ratelimit import RateLimiter
from api.schemas import MessageOut, UserOut
from api.security import hash_secret, hash_token, verify_secret
from db.models import User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(require_app_header)])

CHECK_EMAIL = "If that address can use this, a code is on its way."
BAD_CODE = "That code is wrong or has expired."
BAD_LOGIN = "Wrong email or password."
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _normal_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not EMAIL_RE.fullmatch(value):
        raise ValueError("not a valid email address")
    return value


Email = Annotated[str, AfterValidator(_normal_email)]
Password = Annotated[str, Field(min_length=8, max_length=128)]
Code = Annotated[str, Field(pattern=r"^\d{6}$")]


class RegisterIn(BaseModel):
    email: Email
    password: Password
    website: str = ""  # honeypot: hidden in the form, only bots fill it


class EmailIn(BaseModel):
    email: Email


class VerifyIn(BaseModel):
    email: Email
    code: Code


class LoginIn(BaseModel):
    email: Email
    password: str = Field(max_length=128)


class ResetIn(BaseModel):
    email: Email
    code: Code
    new_password: Password


# Per client address. QUOTE_YARD_AUTH_RATE_LIMIT=0 turns these off (tests).
@lru_cache
def _limiters():
    per_minute = int(os.environ.get("QUOTE_YARD_AUTH_RATE_LIMIT", "20"))
    if per_minute == 0:
        return None
    return {
        "any": RateLimiter(per_minute),
        "login": RateLimiter(10, window=15 * 60),
        "register": RateLimiter(20, window=24 * 60 * 60),
    }


def _limit(request: Request, name: str = "any", key: str = "") -> None:
    limiters = _limiters()
    if limiters is None:
        return
    client = request.client.host if request.client else "unknown"
    wait = limiters[name].check(f"{client}|{key}")
    if wait is not None:
        raise HTTPException(status_code=429, detail="too many attempts, try again later",
                            headers={"Retry-After": str(max(1, int(wait) + 1))})


def _find(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def _queue_code(background: BackgroundTasks, mailer, email: str, code: str | None,
                subject: str, reason: str) -> None:
    if code is None:
        return
    minutes = int(CODE_LIFETIME.total_seconds() // 60)
    body = (f"Your Quote Yard code is {code}.\n\nIt {reason} and expires in {minutes} minutes. "
            "If this wasn't you, you can ignore this email.\n")
    background.add_task(send_safely, mailer, email, subject, body)


def _send_verify(background, mailer, session, user):
    code = issue_code(session, user, "verify_email")
    session.commit()
    _queue_code(background, mailer, user.email, code, "Verify your Quote Yard email",
                "confirms your email address")


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax",
                        secure=cookie_secure(), path="/",
                        max_age=int(SESSION_LIFETIME.total_seconds()))


@router.post("/register", response_model=MessageOut, status_code=202)
def register(body: RegisterIn, request: Request, background: BackgroundTasks,
             session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    """The reply is the same whether or not the address already has an account."""
    _limit(request)
    _limit(request, "register")
    password_hash = hash_secret(body.password)
    if body.website:
        return MessageOut(message=CHECK_EMAIL)
    user = _find(session, body.email)
    if user is None:
        user = User(email=body.email, password_hash=password_hash)
        session.add(user)
        try:
            session.flush()
        except IntegrityError:  # the same address registering at the same moment
            session.rollback()
            return MessageOut(message=CHECK_EMAIL)
    elif user.email_verified_at is None:
        # Whoever enters the emailed code owns the address and this password.
        user.password_hash = password_hash
    else:
        return MessageOut(message=CHECK_EMAIL)
    _send_verify(background, mailer, session, user)
    return MessageOut(message=CHECK_EMAIL)


@router.post("/resend-code", response_model=MessageOut, status_code=202)
def resend_code(body: EmailIn, request: Request, background: BackgroundTasks,
                session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    _limit(request)
    user = _find(session, body.email)
    if user is not None and user.is_active and user.email_verified_at is None:
        _send_verify(background, mailer, session, user)
    return MessageOut(message=CHECK_EMAIL)


@router.post("/verify-email", response_model=UserOut)
def verify_email(body: VerifyIn, request: Request, response: Response,
                 session: Session = Depends(get_write_session)):
    """A right code confirms the address and logs in."""
    _limit(request)
    user = _find(session, body.email)
    if not consume_code(session, user, "verify_email", body.code):
        raise HTTPException(status_code=400, detail=BAD_CODE)
    user.email_verified_at = user.email_verified_at or datetime.now(timezone.utc)
    token = start_session(session, user)
    session.commit()
    _set_cookie(response, token)
    return UserOut.model_validate(user, from_attributes=True)


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, response: Response,
          session: Session = Depends(get_write_session)):
    _limit(request)
    _limit(request, "login", body.email)
    user = _find(session, body.email)
    if not verify_secret(user.password_hash if user else None, body.password) or not user.is_active:
        raise HTTPException(status_code=401, detail=BAD_LOGIN)
    if user.email_verified_at is None:  # only said after the right password
        raise HTTPException(status_code=403, detail="email_not_verified")
    token = start_session(session, user)
    session.commit()
    _set_cookie(response, token)
    return UserOut.model_validate(user, from_attributes=True)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response,
           session: Session = Depends(get_write_session)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        row = session.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(timezone.utc)
            session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(require_user)):
    return UserOut.model_validate(user, from_attributes=True)


@router.post("/forgot-password", response_model=MessageOut, status_code=202)
def forgot_password(body: EmailIn, request: Request, background: BackgroundTasks,
                    session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    _limit(request)
    user = _find(session, body.email)
    if user is not None and user.is_active and user.email_verified_at is not None:
        code = issue_code(session, user, "reset_password")
        session.commit()
        _queue_code(background, mailer, user.email, code, "Reset your Quote Yard password",
                    "lets you choose a new password")
    return MessageOut(message=CHECK_EMAIL)


@router.post("/reset-password", response_model=MessageOut)
def reset_password(body: ResetIn, request: Request,
                   session: Session = Depends(get_write_session)):
    """A new password logs out every device."""
    _limit(request)
    user = _find(session, body.email)
    if not consume_code(session, user, "reset_password", body.code):
        raise HTTPException(status_code=400, detail=BAD_CODE)
    user.password_hash = hash_secret(body.new_password)
    revoke_all_sessions(session, user.id)
    session.commit()
    return MessageOut(message="Password changed. Log in with the new one.")

