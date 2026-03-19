"""Feature: manage_tasks - create and list API.

Optional query filters:
  - ?quote_id=<id>            -- filter tasks by parent quote
  - ?status=todo|doing|done   -- filter by task status
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select

from src.database import get_session
from src.models import Task, TaskStatus
from src.features.manage_tasks.schemas import TaskCreate, TaskRead

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[TaskRead])
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


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: SessionDep):
    task = Task(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
