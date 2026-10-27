from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.deps import get_session
from api.schemas import HealthOut
from db.models import Listing

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(session: Session = Depends(get_session)) -> HealthOut:
    try:
        count = session.scalar(select(func.count()).select_from(Listing))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")
    return HealthOut(status="ok", database="ok", listings=count or 0)