"""Feature: manage_projects - HTML page + CRUD API.

Route map (prefix: /projects)
  GET  /projects/                        Project list page (HTML)
  GET  /projects/api/                    All projects (JSON); filters: ?status=&company_id=
  POST /projects/api/                    Create project (JSON)
  GET  /projects/api/{id}                Single project (JSON)
  PATCH /projects/api/{id}               Update project (JSON)
  DELETE /projects/api/{id}              Delete project (JSON)
"""

from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from src.database import get_session
from src.models import Project, ProjectStatus
from src.features.manage_projects.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _get_or_404(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


# -- HTML routes --------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def projects_page(request: Request, session: SessionDep):
    """Render the project list page."""
    projects = session.exec(select(Project)).all()
    return templates.TemplateResponse(
        request,
        "features/manage_projects/list.html",
        {"projects": projects},
    )


# -- JSON API routes ----------------------------------------------------------

@router.get("/api/", response_model=list[ProjectRead], tags=["Projects API"])
def list_projects(
    session: SessionDep,
    project_status: Optional[ProjectStatus] = Query(None, alias="status"),
    company_id: Optional[int] = Query(None),
):
    stmt = select(Project)
    if project_status:
        stmt = stmt.where(Project.status == project_status)
    if company_id:
        stmt = stmt.where(Project.company_id == company_id)
    return session.exec(stmt).all()


@router.post("/api/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, tags=["Projects API"])
def create_project(payload: ProjectCreate, session: SessionDep):
    project = Project(**payload.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/api/{project_id}", response_model=ProjectRead, tags=["Projects API"])
def get_project(project_id: int, session: SessionDep):
    return _get_or_404(session, project_id)


@router.patch("/api/{project_id}", response_model=ProjectRead, tags=["Projects API"])
def update_project(project_id: int, payload: ProjectUpdate, session: SessionDep):
    project = _get_or_404(session, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/api/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects API"])
def delete_project(project_id: int, session: SessionDep):
    project = _get_or_404(session, project_id)
    session.delete(project)
    session.commit()
