"""Feature: manage_quotes - CRUD API.

Optional query filters:
  - ?status=draft|sent|accepted|cancelled  -- filter by quote status
  - ?project_id=<id>                        -- filter by owning project
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from src.database import get_session
from src.models import Quote, QuoteStatus
from src.features.manage_quotes.schemas import QuoteCreate, QuoteRead, QuoteUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def _get_or_404(session: Session, quote_id: int) -> Quote:
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return quote


@router.get("/", response_model=list[QuoteRead])
def list_quotes(
    session: SessionDep,
    quote_status: Optional[QuoteStatus] = Query(None, alias="status"),
    project_id: Optional[int] = Query(None),
):
    stmt = select(Quote)
    if quote_status:
        stmt = stmt.where(Quote.status == quote_status)
    if project_id:
        stmt = stmt.where(Quote.project_id == project_id)
    return session.exec(stmt).all()


@router.post("/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuoteCreate, session: SessionDep):
    quote = Quote(**payload.model_dump())
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.get("/{quote_id}", response_model=QuoteRead)
def get_quote(quote_id: int, session: SessionDep):
    return _get_or_404(session, quote_id)


@router.patch("/{quote_id}", response_model=QuoteRead)
def update_quote(quote_id: int, payload: QuoteUpdate, session: SessionDep):
    quote = _get_or_404(session, quote_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(quote, field, value)
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(quote_id: int, session: SessionDep):
    quote = _get_or_404(session, quote_id)
    session.delete(quote)
    session.commit()
