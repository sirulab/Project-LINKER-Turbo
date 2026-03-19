"""Feature: submit_timesheet - request / response schemas.

Story 2 AC validation rules:
  - hours_logged must be > 0 (field-level validator)
  - task_id existence is enforced in the router against the DB
  - date_logged must be provided (no default; employee explicitly picks date)
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class TimesheetCreate(BaseModel):
    """Payload sent when an employee submits a timesheet entry."""

    task_id:      int
    hours_logged: float
    date_logged:  date
    description:  Optional[str] = None

    @field_validator("hours_logged")
    @classmethod
    def hours_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("hours_logged must be greater than 0")
        return v


class TimesheetRead(BaseModel):
    """Response shape for a persisted Timesheet record."""

    id:           int
    task_id:      int
    employee_id:  int
    hours_logged: float
    date_logged:  date
    description:  Optional[str]

    model_config = {"from_attributes": True}
