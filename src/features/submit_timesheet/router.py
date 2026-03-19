"""Feature: submit_timesheet - HTMX-driven timesheet entry for employees.

Route map
---------
GET  /timesheet/my
    Renders the full "my tasks" page.
    Query param: ?employee_id=<int>  (placeholder until auth middleware is ready)

GET  /timesheet/tasks/{task_id}/modal
    Returns an HTML fragment (modal body + form) injected by HTMX.
    Query param: ?employee_id=<int>

POST /timesheet/tasks/{task_id}/done
    Form body: employee_id, hours_logged, date_logged, description
    Business logic:
      1. Validate task exists and its project is still active.
      2. Validate employee exists and is_active.
      3. Validate hours_logged > 0 via TimesheetCreate schema.
      4. Persist the Timesheet record.
      5. Auto-transition Task.status:
           todo  -> done  (first-ever log; skips "doing" in this one-shot flow)
           doing -> done
    Returns HTMX OOB-swap toast + HX-Trigger: closeModal header.
"""

from datetime import date
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from src.database import get_session
from src.features.submit_timesheet.queries import get_open_tasks
from src.features.submit_timesheet.schemas import TimesheetCreate
from src.models import (
    Employee,
    ProjectStatus,
    Quote,
    Task,
    TaskStatus,
    Timesheet,
)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

# Resolve template directory relative to this file so the router is
# self-contained and doesn't create a circular import with main.py.
_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# -- Helpers ------------------------------------------------------------------

def _get_task_or_404(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _get_employee_or_404(session: Session, employee_id: int) -> Employee:
    emp = session.get(Employee, employee_id)
    if not emp or not emp.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found or no longer active",
        )
    return emp


def _assert_project_active(task: Task, session: Session) -> None:
    """Raise 409 if the task's project has been completed or archived."""
    quote = session.get(Quote, task.quote_id)
    if quote and quote.project:
        if quote.project.status in (ProjectStatus.completed, ProjectStatus.archived):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot log time: the project is no longer active.",
            )


# -- Routes -------------------------------------------------------------------

@router.get("/my", response_class=HTMLResponse)
def my_tasks_page(
    request: Request,
    session: SessionDep,
    employee_id: Optional[int] = Query(None),
):
    """Full page: my tasks (employee view)."""
    task_data = get_open_tasks(session)
    return templates.TemplateResponse(
        request,
        "features/submit_timesheet/timesheet_form.html",
        {
            "task_data": task_data,
            "employee_id": employee_id,
            "today": date.today().isoformat(),
        },
    )


@router.get("/tasks/{task_id}/modal", response_class=HTMLResponse)
def get_modal_body(
    task_id: int,
    request: Request,
    session: SessionDep,
    employee_id: Optional[int] = Query(None),
):
    """HTMX partial: returns the modal body form for a specific task."""
    task = _get_task_or_404(session, task_id)
    quote = session.get(Quote, task.quote_id)
    project_name = quote.project.name if (quote and quote.project) else "-"

    return templates.TemplateResponse(
        request,
        "features/submit_timesheet/_modal_body.html",
        {
            "task": task,
            "project_name": project_name,
            "employee_id": employee_id,
            "today": date.today().isoformat(),
        },
    )


@router.post("/tasks/{task_id}/done", response_class=HTMLResponse)
def submit_and_mark_done(
    task_id: int,
    session: SessionDep,
    employee_id: int           = Form(...),
    hours_logged: float        = Form(...),
    date_logged: date          = Form(...),
    description: Optional[str] = Form(None),
):
    """Submit timesheet entry and transition task -> done.

    HTMX expects:
      hx-target  = "#task-row-{task_id}"
      hx-swap    = "delete"            (removes the row on success)
    Response includes an OOB-swap toast and HX-Trigger: closeModal header.
    """
    # -- Validation -----------------------------------------------------------
    task     = _get_task_or_404(session, task_id)
    employee = _get_employee_or_404(session, employee_id)
    _assert_project_active(task, session)

    try:
        payload = TimesheetCreate(
            task_id=task_id,
            hours_logged=hours_logged,
            date_logged=date_logged,
            description=description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # -- Persist --------------------------------------------------------------
    timesheet = Timesheet(
        task_id=task_id,
        employee_id=employee.id,
        hours_logged=payload.hours_logged,
        date_logged=payload.date_logged,
        description=payload.description,
    )
    session.add(timesheet)

    # Auto-transition: todo / doing -> done (one-shot "done" action)
    task.status = TaskStatus.done
    session.add(task)
    session.commit()

    # -- HTMX response --------------------------------------------------------
    # The main swap target (#task-row-{task_id}) is deleted by hx-swap="delete".
    # The OOB swap injects a success toast into #toast-container.
    toast_html = (
        f'<div hx-swap-oob="beforeend:#toast-container">'
        f'  <div class="toast align-items-center text-bg-success border-0 show mb-2" role="alert">'
        f'    <div class="d-flex">'
        f'      <div class="toast-body">'
        f'        <i class="bi bi-check-circle-fill me-2"></i>'
        f'        ??? <strong>{payload.hours_logged} ??</strong>?'
        f'        <strong>{task.name}</strong> ????'
        f'      </div>'
        f'      <button type="button" class="btn-close btn-close-white me-2 m-auto"'
        f'              data-bs-dismiss="toast"></button>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )

    response = HTMLResponse(content=toast_html, status_code=200)
    response.headers["HX-Trigger"] = "closeModal"
    return response
