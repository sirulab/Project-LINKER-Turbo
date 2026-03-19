"""Feature: manage_employees - CRUD API.

Business rules enforced:
  - DELETE performs a soft-delete (is_active = False) to preserve Timesheet history.
  - Listing defaults to active employees only; pass ?include_inactive=true to see all.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from src.database import get_session
from src.models import Employee
from src.features.manage_employees.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def _get_or_404(session: Session, employee_id: int) -> Employee:
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.get("/", response_model=list[EmployeeRead])
def list_employees(
    session: SessionDep,
    include_inactive: bool = Query(False, description="Set true to include inactive employees"),
):
    stmt = select(Employee)
    if not include_inactive:
        stmt = stmt.where(Employee.is_active == True)  # noqa: E712
    return session.exec(stmt).all()


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, session: SessionDep):
    employee = Employee(**payload.model_dump())
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, session: SessionDep):
    return _get_or_404(session, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, payload: EmployeeUpdate, session: SessionDep):
    employee = _get_or_404(session, employee_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_employee(employee_id: int, session: SessionDep):
    """Soft-delete: sets is_active=False to preserve historical Timesheet data."""
    employee = _get_or_404(session, employee_id)
    employee.is_active = False
    session.add(employee)
    session.commit()
