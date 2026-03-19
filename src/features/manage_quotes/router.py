"""Feature: manage_quotes - HTML page + CRUD API.

Route map (prefix: /quotes)
  GET  /quotes/                    Quote list page (HTML)
  GET  /quotes/api/                All quotes (JSON); filters: ?status=&project_id=
  POST /quotes/api/                Create quote (JSON)
  GET  /quotes/api/{id}            Single quote (JSON)
  PATCH /quotes/api/{id}           Update quote (JSON)
  DELETE /quotes/api/{id}          Delete quote (JSON)
"""

from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from src.database import get_session
from src.models import Quote, QuoteStatus
from src.features.manage_quotes.schemas import QuoteCreate, QuoteRead, QuoteUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _get_or_404(session: Session, quote_id: int) -> Quote:
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return quote


# -- HTML routes --------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def quotes_page(request: Request, session: SessionDep):
    """Render the quote list page."""
    quotes = session.exec(select(Quote)).all()
    return templates.TemplateResponse(
        request,
        "features/manage_quotes/list.html",
        {"quotes": quotes},
    )


# -- JSON API routes ----------------------------------------------------------

@router.get("/api/", response_model=list[QuoteRead], tags=["Quotes API"])
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


@router.post("/api/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED, tags=["Quotes API"])
def create_quote(payload: QuoteCreate, session: SessionDep):
    quote = Quote(**payload.model_dump())
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.get("/api/{quote_id}", response_model=QuoteRead, tags=["Quotes API"])
def get_quote(quote_id: int, session: SessionDep):
    return _get_or_404(session, quote_id)


@router.patch("/api/{quote_id}", response_model=QuoteRead, tags=["Quotes API"])
def update_quote(quote_id: int, payload: QuoteUpdate, session: SessionDep):
    quote = _get_or_404(session, quote_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(quote, field, value)
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.delete("/api/{quote_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Quotes API"])
def delete_quote(quote_id: int, session: SessionDep):
    quote = _get_or_404(session, quote_id)
    session.delete(quote)
    session.commit()
