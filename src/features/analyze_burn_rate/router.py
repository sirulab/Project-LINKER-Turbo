"""Feature: analyze_burn_rate - HTML pages + JSON API.

Route map (prefix: /burn-rate)
  GET  /burn-rate/                           Dashboard: all projects overview
  GET  /burn-rate/projects/{project_id}      Project detail: per-task donut charts
  GET  /burn-rate/api/projects               All projects (JSON list)
  GET  /burn-rate/api/projects/{project_id}  Single project (JSON)
  GET  /burn-rate/api/tasks/{task_id}        Single task    (JSON)
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from src.database import get_session
from src.features.analyze_burn_rate.schemas import ProjectBurnRateRead, TaskBurnRateRead
from src.features.analyze_burn_rate.services import (
    get_all_projects_burn_rate,
    get_project_burn_rate,
    get_task_burn_rate,
)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# -- HTML routes --------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def burn_rate_dashboard(request: Request, session: SessionDep):
    """Render the burn-rate dashboard showing all projects."""
    projects = get_all_projects_burn_rate(session)
    return templates.TemplateResponse(
        request,
        "features/analyze_burn_rate/dashboard.html",
        {"projects": projects},
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_burn_rate_detail(
    project_id: int,
    request: Request,
    session: SessionDep,
):
    """Render the per-task burn-rate detail page for one project."""
    data = get_project_burn_rate(session, project_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return templates.TemplateResponse(
        request,
        "features/analyze_burn_rate/project_detail.html",
        {"data": data},
    )


# -- JSON API routes ----------------------------------------------------------

@router.get("/api/projects", response_model=list[ProjectBurnRateRead])
def api_all_projects(session: SessionDep):
    """Return burn-rate metrics for every project."""
    return get_all_projects_burn_rate(session)


@router.get("/api/projects/{project_id}", response_model=ProjectBurnRateRead)
def api_project(project_id: int, session: SessionDep):
    """Return burn-rate metrics for a single project."""
    data = get_project_burn_rate(session, project_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return data


@router.get("/api/tasks/{task_id}", response_model=TaskBurnRateRead)
def api_task(task_id: int, session: SessionDep):
    """Return burn-rate metrics for a single task."""
    data = get_task_burn_rate(session, task_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return data
