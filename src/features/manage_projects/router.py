"""Feature: manage_projects - CRUD API.

Optional query filters:
  - ?status=active|completed|archived  -- filter by project status
  - ?company_id=<id>                   -- filter by owning company
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from src.database import get_session
from src.models import Project, ProjectStatus
from src.features.manage_projects.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def _get_or_404(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/", response_model=list[ProjectRead])
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


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: SessionDep):
    project = Project(**payload.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: SessionDep):
    return _get_or_404(session, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, session: SessionDep):
    project = _get_or_404(session, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, session: SessionDep):
    project = _get_or_404(session, project_id)
    session.delete(project)
    session.commit()
