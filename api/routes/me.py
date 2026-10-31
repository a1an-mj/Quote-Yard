from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth import require_app_header, require_user
from api.deps import get_session, get_write_session
from api.routes.products import _get_product
from api.schemas import AlertOut, SavedOut
from db.models import CanonicalProduct, PriceAlert, SavedProduct, User

router = APIRouter(prefix="/me", tags=["me"], dependencies=[Depends(require_app_header)])

ProductId = Annotated[int, Path(ge=1, le=2_147_483_647)]


class AlertIn(BaseModel):
    target_price: int = Field(gt=0, le=100_000_000)


def _require_product(session: Session, product_id: int) -> None:
    if session.get(CanonicalProduct, product_id) is None:
        raise HTTPException(status_code=404, detail="product not found")


def _saved_out(session, row) -> SavedOut:
    return SavedOut(product=_get_product(session, row.canonical_product_id),
                    price_when_saved=row.price_when_saved, saved_at=row.created_at)


def _alert_out(session, row) -> AlertOut:
    return AlertOut(product=_get_product(session, row.canonical_product_id),
                    target_price=row.target_price, last_notified_at=row.last_notified_at,
                    created_at=row.created_at)


@router.get("/saved", response_model=list[SavedOut])
def list_saved(user: User = Depends(require_user), session: Session = Depends(get_session)):
    rows = session.scalars(select(SavedProduct).where(SavedProduct.user_id == user.id)
                           .order_by(SavedProduct.created_at.desc(), SavedProduct.id.desc()))
    return [_saved_out(session, row) for row in rows]


@router.put("/saved/{product_id}", response_model=SavedOut)
def save_product(product_id: ProductId, user: User = Depends(require_user),
                 session: Session = Depends(get_write_session)):
    """Saving again changes nothing."""
    _require_product(session, product_id)
    query = select(SavedProduct).where(SavedProduct.user_id == user.id,
                                       SavedProduct.canonical_product_id == product_id)
    row = session.scalar(query)
    if row is None:
        row = SavedProduct(user_id=user.id, canonical_product_id=product_id,
                           price_when_saved=_get_product(session, product_id).min_price)
        session.add(row)
        try:
            session.commit()
        except IntegrityError:  # the same save arriving twice at once
            session.rollback()
            row = session.scalar(query)
    return _saved_out(session, row)


@router.delete("/saved/{product_id}", status_code=204)
def unsave_product(product_id: ProductId, user: User = Depends(require_user),
                   session: Session = Depends(get_write_session)):
    session.execute(delete(SavedProduct).where(SavedProduct.user_id == user.id,
                                               SavedProduct.canonical_product_id == product_id))
    session.commit()


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(user: User = Depends(require_user), session: Session = Depends(get_session)):
    rows = session.scalars(select(PriceAlert).where(PriceAlert.user_id == user.id)
                           .order_by(PriceAlert.created_at.desc(), PriceAlert.id.desc()))
    return [_alert_out(session, row) for row in rows]


@router.put("/alerts/{product_id}", response_model=AlertOut)
def set_alert(product_id: ProductId, body: AlertIn, user: User = Depends(require_user),
              session: Session = Depends(get_write_session)):
    """Create the alert or change its target. A new target can notify again."""
    _require_product(session, product_id)
    query = select(PriceAlert).where(PriceAlert.user_id == user.id,
                                     PriceAlert.canonical_product_id == product_id)
    row = session.scalar(query)
    if row is None:
        row = PriceAlert(user_id=user.id, canonical_product_id=product_id,
                         target_price=body.target_price)
        session.add(row)
    elif row.target_price != body.target_price:
        row.target_price = body.target_price
        row.last_notified_price = None
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        row = session.scalar(query)
    return _alert_out(session, row)


@router.delete("/alerts/{product_id}", status_code=204)
def delete_alert(product_id: ProductId, user: User = Depends(require_user),
                 session: Session = Depends(get_write_session)):
    session.execute(delete(PriceAlert).where(PriceAlert.user_id == user.id,
                                             PriceAlert.canonical_product_id == product_id))
    session.commit()
