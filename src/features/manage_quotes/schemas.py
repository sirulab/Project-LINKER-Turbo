"""Feature: manage_quotes - request / response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from src.models import QuoteStatus


class QuoteCreate(BaseModel):
    quote_number: str
    status:       QuoteStatus    = QuoteStatus.draft
    total_amount: Decimal        = Decimal("0.00")
    valid_until:  Optional[date] = None
    project_id:   Optional[int]  = None


class QuoteUpdate(BaseModel):
    quote_number: Optional[str]         = None
    status:       Optional[QuoteStatus] = None
    total_amount: Optional[Decimal]     = None
    valid_until:  Optional[date]        = None
    project_id:   Optional[int]         = None


class QuoteRead(BaseModel):
    id:           int
    quote_number: str
    status:       QuoteStatus
    total_amount: Decimal
    valid_until:  Optional[date]
    created_at:   datetime
    project_id:   Optional[int]

    model_config = {"from_attributes": True}
