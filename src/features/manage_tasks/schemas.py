"""Feature: manage_tasks - request / response schemas."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from src.models import TaskStatus


class TaskCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    quantity:    float
    unit_price:  Decimal
    status:      TaskStatus    = TaskStatus.todo
    quote_id:    Optional[int] = None


class TaskRead(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    quantity:    float
    unit_price:  Decimal
    status:      TaskStatus
    quote_id:    Optional[int]

    model_config = {"from_attributes": True}
