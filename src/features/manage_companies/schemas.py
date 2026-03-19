"""Feature: manage_companies - request / response schemas."""

from typing import Optional

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name:    str
    tax_id:  str
    email:   Optional[str] = None
    phone:   Optional[str] = None
    address: Optional[str] = None


class CompanyUpdate(BaseModel):
    name:    Optional[str] = None
    tax_id:  Optional[str] = None
    email:   Optional[str] = None
    phone:   Optional[str] = None
    address: Optional[str] = None


class CompanyRead(BaseModel):
    id:      int
    name:    str
    tax_id:  str
    email:   Optional[str]
    phone:   Optional[str]
    address: Optional[str]

    model_config = {"from_attributes": True}
