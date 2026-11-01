"""The review page's API: invite shops, approve them, and remove offers."""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import require_admin, require_app_header
from api.deps import get_session, get_write_session
from api.mailer import get_mailer, send_safely
from api.routes.auth import Email, _limit
from api.routes.vendor import audit, issue_token, offer_state, site_url, today_in_india
from db.models import CanonicalProduct, User, Vendor, VendorAuditLog, VendorOffer, VendorToken

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_app_header), Depends(require_admin)])

INVITE_LIFETIME = timedelta(days=7)
Id = Annotated[int, Path(ge=1, le=2_147_483_647)]
# status now -> the decisions allowed from it
DECISIONS = {
    "approve": ("approved", {"pending", "rejected"}),
    "reject": ("rejected", {"pending"}),
    "suspend": ("suspended", {"approved"}),
    "reinstate": ("approved", {"suspended"}),
}
DECISION_MAIL = {
    "approved": "Your shop is approved. You can now log in and publish offers.",
    "rejected": "We couldn't approve your shop.",
    "suspended": "Your shop has been suspended and its offers are hidden.",
}


class InviteIn(BaseModel):
    email: Email


class InviteOut(BaseModel):
    id: int
    email: str
    state: str  # waiting, joined, expired, cancelled
    expires_at: datetime
    created_at: datetime


class AdminVendorOut(BaseModel):
    id: int
    email: str
    shop_name: str
    owner_name: str
    phone: str
    address: str
    town: str
    district: str
    gst_number: str | None
    status: str
    created_at: datetime
    reviewed_at: datetime | None


class AdminOfferOut(BaseModel):
    id: int
    shop_name: str
    product_id: int
    product_name: str
    price: int
    starts_on: date
    ends_on: date
    state: str


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject", "suspend", "reinstate"]


class AuditOut(BaseModel):
    id: int
    actor: str
    action: str
    vendor_id: int | None
    offer_id: int | None
    detail: dict | None
    created_at: datetime


def _invite_out(row: VendorToken) -> InviteOut:
    if row.used_at is not None:
        state = "joined"
    elif row.revoked_at is not None:
        state = "cancelled"
    elif row.expires_at <= datetime.now(timezone.utc):
        state = "expired"
    else:
        state = "waiting"
    return InviteOut(id=row.id, email=row.email, state=state, expires_at=row.expires_at,
                     created_at=row.created_at)


@router.get("/invites", response_model=list[InviteOut])
def list_invites(session: Session = Depends(get_session)):
    rows = session.scalars(select(VendorToken).where(VendorToken.purpose == "invite")
                           .order_by(VendorToken.id.desc()).limit(100))
    return [_invite_out(row) for row in rows]


@router.post("/invites", response_model=InviteOut, status_code=201)
def create_invite(body: InviteIn, request: Request, background: BackgroundTasks,
                  admin: User = Depends(require_admin),
                  session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    """The link goes only to that address, so opening it proves the shop owns the address."""
    _limit(request)
    if session.scalar(select(Vendor.id).where(Vendor.email == body.email)) is not None:
        raise HTTPException(status_code=409, detail="A shop with this email already exists.")
    token = issue_token(session, body.email, "invite", INVITE_LIFETIME)
    audit(session, f"admin:{admin.email}", "invited", email=body.email)
    session.commit()
    row = session.scalar(select(VendorToken).where(VendorToken.email == body.email,
                                                   VendorToken.purpose == "invite")
                         .order_by(VendorToken.id.desc()).limit(1))
    link = f"{site_url(request)}/vendor/join#{token}"
    background.add_task(send_safely, mailer, body.email, "List your shop's offers on Quote Yard",
                        f"You're invited to list your shop's offers on Quote Yard.\n\n"
                        f"Open this link to set up your shop:\n\n{link}\n\n"
                        "It works once and expires in 7 days.\n")
    return _invite_out(row)


@router.delete("/invites/{invite_id}", status_code=204)
def cancel_invite(invite_id: Id, admin: User = Depends(require_admin),
                  session: Session = Depends(get_write_session)):
    row = session.scalar(select(VendorToken).where(VendorToken.id == invite_id,
                                                   VendorToken.purpose == "invite"))
    if row is None:
        raise HTTPException(status_code=404, detail="invite not found")
    if row.used_at is None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        audit(session, f"admin:{admin.email}", "invite_cancelled", email=row.email)
        session.commit()


@router.get("/vendors", response_model=list[AdminVendorOut])
def list_vendors(session: Session = Depends(get_session)):
    rows = session.scalars(select(Vendor).order_by(Vendor.status != "pending", Vendor.id.desc()))
    return [AdminVendorOut.model_validate(row, from_attributes=True) for row in rows]


@router.post("/vendors/{vendor_id}/decision", response_model=AdminVendorOut)
def decide(vendor_id: Id, body: DecisionIn, background: BackgroundTasks,
           admin: User = Depends(require_admin),
           session: Session = Depends(get_write_session), mailer=Depends(get_mailer)):
    vendor = session.scalar(select(Vendor).where(Vendor.id == vendor_id).with_for_update())
    if vendor is None:
        raise HTTPException(status_code=404, detail="shop not found")
    new_status, allowed_from = DECISIONS[body.decision]
    if vendor.status not in allowed_from:
        raise HTTPException(status_code=409, detail=f"A shop that is {vendor.status} can't be changed this way.")
    before, vendor.status = vendor.status, new_status
    vendor.reviewed_at = datetime.now(timezone.utc)
    audit(session, f"admin:{admin.email}", body.decision, vendor.id, before=before, after=new_status)
    session.commit()
    background.add_task(send_safely, mailer, vendor.email, "Your shop on Quote Yard",
                        f"Hi {vendor.owner_name},\n\n{DECISION_MAIL[new_status]}\n")
    return AdminVendorOut.model_validate(vendor, from_attributes=True)


@router.get("/offers", response_model=list[AdminOfferOut])
def running_offers(session: Session = Depends(get_session)):
    today = today_in_india()
    rows = session.execute(
        select(VendorOffer, Vendor.shop_name, CanonicalProduct.name)
        .join(Vendor, Vendor.id == VendorOffer.vendor_id)
        .join(CanonicalProduct, CanonicalProduct.id == VendorOffer.canonical_product_id)
        .where(VendorOffer.closed_at.is_(None), VendorOffer.ends_on >= today)
        .order_by(VendorOffer.updated_at.desc(), VendorOffer.id.desc()).limit(200)
    ).all()
    return [
        AdminOfferOut(id=o.id, shop_name=shop, product_id=o.canonical_product_id, product_name=name,
                      price=o.price, starts_on=o.starts_on, ends_on=o.ends_on, state=offer_state(o, today))
        for o, shop, name in rows
    ]


@router.delete("/offers/{offer_id}", status_code=204)
def remove_offer(offer_id: Id, admin: User = Depends(require_admin),
                 session: Session = Depends(get_write_session)):
    offer = session.scalar(select(VendorOffer).where(VendorOffer.id == offer_id,
                                                     VendorOffer.closed_at.is_(None)).with_for_update())
    if offer is None:
        raise HTTPException(status_code=404, detail="offer not found")
    offer.closed_at, offer.closed_by = datetime.now(timezone.utc), "admin"
    audit(session, f"admin:{admin.email}", "offer_removed", offer.vendor_id, offer.id, price=offer.price)
    session.commit()


@router.get("/audit", response_model=list[AuditOut])
def audit_log(session: Session = Depends(get_session)):
    rows = session.scalars(select(VendorAuditLog).order_by(VendorAuditLog.id.desc()).limit(100))
    return [AuditOut.model_validate(row, from_attributes=True) for row in rows]
