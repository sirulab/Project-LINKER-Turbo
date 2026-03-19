"""Feature: manage_tasks - HTML page + create and list API.

Route map (prefix: /tasks)
  GET  /tasks/           Task list page (HTML)
  GET  /tasks/api/       All tasks (JSON); filters: ?quote_id=&status=
  POST /tasks/api/       Create task (JSON)
"""

from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from src.database import get_session
from src.models import Task, TaskStatus
from src.features.manage_tasks.schemas import TaskCreate, TaskRead

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# -- HTML routes --------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def tasks_page(request: Request, session: SessionDep):
    """Render the task list page."""
    tasks = session.exec(select(Task)).all()
    return templates.TemplateResponse(
        request,
        "features/manage_tasks/list.html",
        {"tasks": tasks},
    )


# -- JSON API routes ----------------------------------------------------------

@router.get("/api/", response_model=list[TaskRead])
def list_tasks(
    session: SessionDep,
    quote_id: Optional[int] = Query(None),
    task_status: Optional[TaskStatus] = Query(None, alias="status"),
):
    stmt = select(Task)
    if quote_id:
        stmt = stmt.where(Task.quote_id == quote_id)
    if task_status:
        stmt = stmt.where(Task.status == task_status)
    return session.exec(stmt).all()


@router.post("/api/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: SessionDep):
    task = Task(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
