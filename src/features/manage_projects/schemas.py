"""Feature: manage_projects - request / response schemas."""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from src.models import ProjectStatus


class ProjectCreate(BaseModel):
    name:        str
    description: Optional[str]          = None
    status:      ProjectStatus           = ProjectStatus.active
    start_date:  Optional[date]          = None
    company_id:  Optional[int]           = None


class ProjectUpdate(BaseModel):
    name:        Optional[str]           = None
    description: Optional[str]          = None
    status:      Optional[ProjectStatus] = None
    start_date:  Optional[date]          = None
    company_id:  Optional[int]           = None


class ProjectRead(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    status:      ProjectStatus
    start_date:  Optional[date]
    company_id:  Optional[int]

    model_config = {"from_attributes": True}
