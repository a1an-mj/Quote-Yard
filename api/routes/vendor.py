"""Local shops: joining by invite, logging in, and managing their own offers."""

import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request, Response
from pydantic import AfterValidator, BaseModel, Field, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth import SESSION_LIFETIME, cookie_secure, require_app_header
from api.deps import get_session, get_write_session
from api.filters import MAX_QUERY_WORDS, escape_like
from api.mailer import get_mailer, send_safely
from api.routes.auth import BAD_LOGIN, CHECK_EMAIL, Email, Password, _limit
from api.routes.products import _get_product, _product_out, _product_query
from api.schemas import MessageOut, ProductOut
from api.security import hash_secret, hash_token, new_session_token, verify_secret
from db.models import CanonicalProduct, Vendor, VendorAuditLog, VendorOffer, VendorSession, VendorToken

router = APIRouter(prefix="/vendor", tags=["vendor"], dependencies=[Depends(require_app_header)])

VENDOR_COOKIE = "qy_vendor_session"
RESET_LIFETIME = timedelta(hours=1)
BAD_LINK = "This link is wrong, has expired or was already used."
MAX_OPEN_OFFERS = 200
MAX_OFFER_DAYS = 31
MAX_START_AHEAD_DAYS = 30
# Offers go live without a person checking them, so a price far from the
# stores' lowest is refused as a likely typing mistake.
MIN_PRICE_PERCENT = 50
MAX_PRICE_PERCENT = 150

DISTRICTS = ("Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam",
             "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram",
             "Thrissur", "Wayanad")
GST_RE = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]")

OfferId = Annotated[int, Path(ge=1, le=2_147_483_647)]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def today_in_india() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def _phone(value: str) -> str:
    digits = re.sub(r"[\s()+-]", "", value)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if not re.fullmatch(r"[2-9]\d{9}", digits):
        raise ValueError("not a valid Indian phone number")
    return digits


def _district(value: str) -> str:
    if value not in DISTRICTS:
        raise ValueError("not a Kerala district")
    return value


def _gst(value: str | None) -> str | None:
    value = (value or "").strip().upper()
    if value and not GST_RE.fullmatch(value):
        raise ValueError("not a valid GST number")
    return value or None


def _text(limit: int):
    def check(value: str) -> str:
        value = " ".join(value.split())
        if not 2 <= len(value) <= limit:
            raise ValueError(f"must be 2 to {limit} characters")
        return value
    return AfterValidator(check)


class JoinIn(BaseModel):
    token: str = Field(max_length=100)
    password: Password
    shop_name: Annotated[str, _text(80)]
    owner_name: Annotated[str, _text(80)]
    phone: Annotated[str, AfterValidator(_phone)]
    address: Annotated[str, _text(200)]
    town: Annotated[str, _text(60)]
    district: Annotated[str, AfterValidator(_district)]
    gst_number: Annotated[str | None, AfterValidator(_gst)] = None


class LoginIn(BaseModel):
    email: Email
    password: str = Field(max_length=128)


class EmailIn(BaseModel):
    email: Email


class ResetIn(BaseModel):
    token: str = Field(max_length=100)
    new_password: Password


class OfferIn(BaseModel):
    price: int = Field(gt=0, le=100_000_000)
    starts_on: date
    ends_on: date

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.ends_on < self.starts_on:
            raise ValueError("the end date is before the start date")
        return self


class NewOfferIn(OfferIn):
    product_id: int = Field(ge=1, le=2_147_483_647)


class VendorOut(BaseModel):
    email: str
    shop_name: str
    owner_name: str
    phone: str
    address: str
    town: str
    district: str
    status: str


class VendorOfferOut(BaseModel):
    id: int
    product: ProductOut
    price: int
    starts_on: date
    ends_on: date
    state: str  # scheduled, live, expired, closed
    closed_by: str | None


def audit(session: Session, actor: str, action: str, vendor_id: int | None = None,
          offer_id: int | None = None, **detail) -> None:
    session.add(VendorAuditLog(actor=actor, action=action, vendor_id=vendor_id,
                               offer_id=offer_id, detail=detail or None))


def offer_state(offer: VendorOffer, today: date) -> str:
    if offer.closed_at is not None:
        return "closed"
    if offer.ends_on < today:
        return "expired"
    return "scheduled" if offer.starts_on > today else "live"


def _offer_out(session: Session, offer: VendorOffer) -> VendorOfferOut:
    return VendorOfferOut(
        id=offer.id, product=_get_product(session, offer.canonical_product_id), price=offer.price,
        starts_on=offer.starts_on, ends_on=offer.ends_on,
        state=offer_state(offer, today_in_india()), closed_by=offer.closed_by,
    )


def require_vendor(request: Request, session: Session = Depends(get_session)) -> Vendor:
    token = request.cookies.get(VENDOR_COOKIE)
    vendor = None
    if token:
        vendor = session.scalar(
            select(Vendor)
            .join(VendorSession, VendorSession.vendor_id == Vendor.id)
            .where(VendorSession.token_hash == hash_token(token),
                   VendorSession.revoked_at.is_(None),
                   VendorSession.expires_at > _now())
        )
    if vendor is None:
        raise HTTPException(status_code=401, detail="not logged in")
    return vendor


def require_approved(vendor: Vendor = Depends(require_vendor)) -> Vendor:
    if vendor.status != "approved":
        raise HTTPException(status_code=403, detail="This shop is not approved to publish offers.")
    return vendor


def _start_session(session: Session, vendor: Vendor, response: Response) -> None:
    token = new_session_token()
    session.add(VendorSession(vendor_id=vendor.id, token_hash=hash_token(token),
                              expires_at=_now() + SESSION_LIFETIME))
    vendor.last_login_at = _now()
    session.commit()
    response.set_cookie(VENDOR_COOKIE, token, httponly=True, samesite="lax",
                        secure=cookie_secure(), path="/",
                        max_age=int(SESSION_LIFETIME.total_seconds()))


def issue_token(session: Session, email: str, purpose: str, lifetime: timedelta) -> str:
    """A new one-time link token, cancelling earlier ones for this address and purpose."""
    session.execute(
        update(VendorToken)
        .where(VendorToken.email == email, VendorToken.purpose == purpose,
               VendorToken.used_at.is_(None), VendorToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    token = new_session_token()
    session.add(VendorToken(email=email, purpose=purpose, token_hash=hash_token(token),
                            expires_at=_now() + lifetime))
    return token


def _take_token(session: Session, token: str, purpose: str) -> VendorToken:
    row = session.scalar(
        select(VendorToken)
        .where(VendorToken.token_hash == hash_token(token), VendorToken.purpose == purpose,
               VendorToken.used_at.is_(None), VendorToken.revoked_at.is_(None),
               VendorToken.expires_at > _now())
        .with_for_update()
    )
    if row is None:
        raise HTTPException(status_code=400, detail=BAD_LINK)
    return row


def site_url(request: Request) -> str:
    return (os.environ.get("QUOTE_YARD_SITE_URL") or str(request.base_url)).rstrip("/")


@router.post("/join", response_model=VendorOut, status_code=201)
def join(body: JoinIn, request: Request, response: Response,
         session: Session = Depends(get_write_session)):
    """The emailed invite proves the address. The shop then waits for review."""
    _limit(request)
    invite = _take_token(session, body.token, "invite")
    invite.used_at = _now()
    vendor = Vendor(
        email=invite.email, password_hash=hash_secret(body.password), shop_name=body.shop_name,
        owner_name=body.owner_name, phone=body.phone, address=body.address, town=body.town,
        district=body.district, gst_number=body.gst_number,
    )
    session.add(vendor)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail=BAD_LINK) from None
    audit(session, f"vendor:{vendor.id}", "joined", vendor.id)
    _start_session(session, vendor, response)
    return VendorOut.model_validate(vendor, from_attributes=True)


@router.post("/login", response_model=VendorOut)
def login(body: LoginIn, request: Request, response: Response,
          session: Session = Depends(get_write_session)):
    """Rejected and suspended shops can still log in, to see their status."""
    _limit(request)
    _limit(request, "login", f"vendor|{body.email}")
    vendor = session.scalar(select(Vendor).where(Vendor.email == body.email))
    if not verify_secret(vendor.password_hash if vendor else None, body.password):
        raise HTTPException(status_code=401, detail=BAD_LOGIN)
    _start_session(session, vendor, response)
    return VendorOut.model_validate(vendor, from_attributes=True)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session: Session = Depends(get_write_session)):
    token = request.cookies.get(VENDOR_COOKIE)
    if token:
        session.execute(
            update(VendorSession)
            .where(VendorSession.token_hash == hash_token(token), VendorSession.revoked_at.is_(None))
            .values(revoked_at=_now())
        )
        session.commit()
    response.delete_cookie(VENDOR_COOKIE, path="/")


@router.get("/me", response_model=VendorOut)
def me(vendor: Vendor = Depends(require_vendor)):
    return VendorOut.model_validate(vendor, from_attributes=True)


@router.post("/forgot-password", response_model=MessageOut, status_code=202)
def forgot_password(body: EmailIn, request: Request, background: BackgroundTasks,
                    session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    """The reply is the same whether or not the address has a shop."""
    _limit(request)
    _limit(request, "login", f"vendor-reset|{body.email}")
    vendor = session.scalar(select(Vendor).where(Vendor.email == body.email))
    if vendor is not None:
        token = issue_token(session, vendor.email, "reset_password", RESET_LIFETIME)
        session.commit()
        link = f"{site_url(request)}/vendor/reset#{token}"
        background.add_task(send_safely, mailer, vendor.email, "Reset your Quote Yard shop password",
                            f"Open this link to choose a new password:\n\n{link}\n\n"
                            "It works once and expires in 1 hour. If this wasn't you, ignore this email.\n")
    return MessageOut(message=CHECK_EMAIL)


@router.post("/reset-password", response_model=MessageOut)
def reset_password(body: ResetIn, request: Request, session: Session = Depends(get_write_session)):
    """A new password logs out every device."""
    _limit(request)
    row = _take_token(session, body.token, "reset_password")
    vendor = session.scalar(select(Vendor).where(Vendor.email == row.email))
    if vendor is None:
        raise HTTPException(status_code=400, detail=BAD_LINK)
    row.used_at = _now()
    vendor.password_hash = hash_secret(body.new_password)
    session.execute(
        update(VendorSession)
        .where(VendorSession.vendor_id == vendor.id, VendorSession.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    audit(session, f"vendor:{vendor.id}", "password_reset", vendor.id)
    session.commit()
    return MessageOut(message="Password changed. Log in with the new one.")


@router.get("/products", response_model=list[ProductOut])
def find_products(q: str = Query(min_length=2, max_length=100),
                  _: Vendor = Depends(require_vendor), session: Session = Depends(get_session)):
    """Offers can only be made on products that stores currently list."""
    stmt = _product_query()
    text = func.concat_ws(" ", CanonicalProduct.name, CanonicalProduct.brand, CanonicalProduct.model)
    for word in q.split()[:MAX_QUERY_WORDS]:
        stmt = stmt.where(text.ilike(f"%{escape_like(word)}%", escape="\\"))
    rows = session.execute(stmt.order_by(func.lower(CanonicalProduct.name), CanonicalProduct.id).limit(20))
    return [_product_out(*row) for row in rows.all()]


@router.get("/offers", response_model=list[VendorOfferOut])
def my_offers(vendor: Vendor = Depends(require_vendor), session: Session = Depends(get_session)):
    rows = session.scalars(
        select(VendorOffer).where(VendorOffer.vendor_id == vendor.id)
        .order_by(VendorOffer.closed_at.is_not(None), VendorOffer.ends_on.desc(), VendorOffer.id.desc())
        .limit(MAX_OPEN_OFFERS * 2)
    )
    return [_offer_out(session, row) for row in rows]


def _check_offer(session: Session, product_id: int, body: OfferIn, check_start: bool) -> None:
    """The automatic checks. Nobody reviews an offer before customers see it."""
    today = today_in_india()
    if body.ends_on < today:
        raise HTTPException(status_code=422, detail="The end date has already passed.")
    if check_start and body.starts_on < today:
        raise HTTPException(status_code=422, detail="The start date has already passed.")
    if body.starts_on > today + timedelta(days=MAX_START_AHEAD_DAYS):
        raise HTTPException(status_code=422, detail=f"An offer can start at most {MAX_START_AHEAD_DAYS} days ahead.")
    if (body.ends_on - body.starts_on).days + 1 > MAX_OFFER_DAYS:
        raise HTTPException(status_code=422, detail=f"An offer can run for at most {MAX_OFFER_DAYS} days.")
    low = _get_product(session, product_id).min_price
    if low is None:
        raise HTTPException(status_code=422, detail="No store has a current price for this product, so an offer can't be checked.")
    if not low * MIN_PRICE_PERCENT <= body.price * 100 <= low * MAX_PRICE_PERCENT:
        raise HTTPException(
            status_code=422,
            detail=f"That price is too far from the lowest store price (Rs {low}). "
                   "Please check it for a typing mistake.")


@router.post("/offers", response_model=VendorOfferOut, status_code=201)
def create_offer(body: NewOfferIn, request: Request, vendor: Vendor = Depends(require_approved),
                 session: Session = Depends(get_write_session)):
    _limit(request)
    today = today_in_india()
    _check_offer(session, body.product_id, body, check_start=True)
    existing = session.scalar(
        select(VendorOffer).where(VendorOffer.vendor_id == vendor.id,
                                  VendorOffer.canonical_product_id == body.product_id,
                                  VendorOffer.closed_at.is_(None))
    )
    if existing is not None:
        if existing.ends_on >= today:
            raise HTTPException(status_code=409, detail="You already have an offer on this product. Edit that one.")
        existing.closed_at, existing.closed_by = _now(), "replaced"
        session.flush()
    running = session.scalar(
        select(func.count(VendorOffer.id))
        .where(VendorOffer.vendor_id == vendor.id, VendorOffer.closed_at.is_(None),
               VendorOffer.ends_on >= today)
    )
    if running >= MAX_OPEN_OFFERS:
        raise HTTPException(status_code=409, detail=f"A shop can have at most {MAX_OPEN_OFFERS} running offers.")
    offer = VendorOffer(vendor_id=vendor.id, canonical_product_id=body.product_id, price=body.price,
                        starts_on=body.starts_on, ends_on=body.ends_on)
    session.add(offer)
    try:
        session.flush()
    except IntegrityError:  # the same offer submitted twice at once
        session.rollback()
        raise HTTPException(status_code=409, detail="You already have an offer on this product. Edit that one.") from None
    audit(session, f"vendor:{vendor.id}", "offer_created", vendor.id, offer.id, price=offer.price,
          product_id=offer.canonical_product_id, starts_on=str(offer.starts_on), ends_on=str(offer.ends_on))
    session.commit()
    return _offer_out(session, offer)


def _own_open_offer(session: Session, vendor: Vendor, offer_id: int) -> VendorOffer:
    offer = session.scalar(select(VendorOffer).where(
        VendorOffer.id == offer_id, VendorOffer.vendor_id == vendor.id,
        VendorOffer.closed_at.is_(None)).with_for_update())
    if offer is None:
        raise HTTPException(status_code=404, detail="offer not found")
    return offer


@router.put("/offers/{offer_id}", response_model=VendorOfferOut)
def update_offer(offer_id: OfferId, body: OfferIn, request: Request,
                 vendor: Vendor = Depends(require_approved),
                 session: Session = Depends(get_write_session)):
    _limit(request)
    offer = _own_open_offer(session, vendor, offer_id)
    _check_offer(session, offer.canonical_product_id, body, check_start=body.starts_on != offer.starts_on)
    before = dict(price=offer.price, starts_on=str(offer.starts_on), ends_on=str(offer.ends_on))
    offer.price, offer.starts_on, offer.ends_on = body.price, body.starts_on, body.ends_on
    offer.updated_at = _now()
    audit(session, f"vendor:{vendor.id}", "offer_updated", vendor.id, offer.id, before=before,
          price=offer.price, starts_on=str(offer.starts_on), ends_on=str(offer.ends_on))
    session.commit()
    return _offer_out(session, offer)


@router.delete("/offers/{offer_id}", status_code=204)
def close_offer(offer_id: OfferId, vendor: Vendor = Depends(require_vendor),
                session: Session = Depends(get_write_session)):
    """Allowed in any status: a shop can always take its own price down."""
    offer = _own_open_offer(session, vendor, offer_id)
    offer.closed_at, offer.closed_by = _now(), "vendor"
    audit(session, f"vendor:{vendor.id}", "offer_closed", vendor.id, offer.id)
    session.commit()
