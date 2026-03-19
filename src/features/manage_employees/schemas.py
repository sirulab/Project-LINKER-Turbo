"""Feature: manage_employees - request / response schemas."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr

from src.models import EmployeeRole


class EmployeeCreate(BaseModel):
    name:        str
    email:       EmailStr
    role:        EmployeeRole  = EmployeeRole.employee
    hourly_rate: Decimal


class EmployeeUpdate(BaseModel):
    name:        Optional[str]          = None
    email:       Optional[EmailStr]     = None
    role:        Optional[EmployeeRole] = None
    hourly_rate: Optional[Decimal]      = None
    is_active:   Optional[bool]         = None


class EmployeeRead(BaseModel):
    id:          int
    name:        str
    email:       str
    role:        EmployeeRole
    hourly_rate: Decimal
    is_active:   bool

    model_config = {"from_attributes": True}
