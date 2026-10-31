from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deals import todays_deals
from api.deps import get_session
from api.schemas import DealOut

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/deals", response_model=list[DealOut])
def public_deals(session: Session = Depends(get_session)):
    """Up to 5 of today's deals. No store links: those are behind the login."""
    return [
        DealOut(kind=d.kind, name=d.name, brand=d.brand, retailer=d.retailer, price=d.price,
                compared_price=d.compared_price, compared_retailer=d.compared_retailer,
                saving=d.saving, label=d.label, checked_at=d.checked_at)
        for d in todays_deals(session)
    ]
