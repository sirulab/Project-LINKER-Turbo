"""Feature: manage_companies - HTML page + CRUD API.

Route map (prefix: /companies)
  GET  /companies/               Company list page (HTML)
  GET  /companies/api/           All companies (JSON)
  POST /companies/api/           Create company (JSON)
  GET  /companies/api/{id}       Single company (JSON)
  PATCH /companies/api/{id}      Update company (JSON)
  DELETE /companies/api/{id}     Delete company (JSON)
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from src.database import get_session
from src.models import Company
from src.features.manage_companies.schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _get_or_404(session: Session, company_id: int) -> Company:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


# -- HTML routes --------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def companies_page(request: Request, session: SessionDep):
    """Render the company list page."""
    companies = session.exec(select(Company)).all()
    return templates.TemplateResponse(
        request,
        "features/manage_companies/list.html",
        {"companies": companies},
    )


# -- JSON API routes ----------------------------------------------------------

@router.get("/api/", response_model=list[CompanyRead])
def list_companies(session: SessionDep):
    return session.exec(select(Company)).all()


@router.post("/api/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, session: SessionDep):
    company = Company(**payload.model_dump())
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.get("/api/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, session: SessionDep):
    return _get_or_404(session, company_id)


@router.patch("/api/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, session: SessionDep):
    company = _get_or_404(session, company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.delete("/api/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, session: SessionDep):
    company = _get_or_404(session, company_id)
    session.delete(company)
    session.commit()
