"""Feature: manage_companies - CRUD API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.database import get_session
from src.models import Company
from src.features.manage_companies.schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def _get_or_404(session: Session, company_id: int) -> Company:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.get("/", response_model=list[CompanyRead])
def list_companies(session: SessionDep):
    return session.exec(select(Company)).all()


@router.post("/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, session: SessionDep):
    company = Company(**payload.model_dump())
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, session: SessionDep):
    return _get_or_404(session, company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, session: SessionDep):
    company = _get_or_404(session, company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, session: SessionDep):
    company = _get_or_404(session, company_id)
    session.delete(company)
    session.commit()
