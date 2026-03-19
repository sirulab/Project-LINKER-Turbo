"""Feature: analyze_burn_rate - business-logic layer.

Public API
----------
get_task_burn_rate(session, task_id)       -> TaskBurnRateRead | None
get_project_burn_rate(session, project_id) -> ProjectBurnRateRead | None
get_all_projects_burn_rate(session)        -> list[ProjectBurnRateRead]

Design notes
------------
* All queries eagerly resolve ORM relationships so callers receive
  plain Pydantic objects (no lazy-load surprises outside the Session).
* Business rule (AC 3): burn_warning is only raised when the task is
  still open (not done); a completed task with >80% logged is expected.
"""

from sqlmodel import Session, select

from src.models import Project, Quote, QuoteStatus, Task, TaskStatus
from src.features.analyze_burn_rate.schemas import (
    ProjectBurnRateRead,
    TaskBurnRateRead,
)


# -- Helpers ------------------------------------------------------------------

def _compute_task_metrics(task: Task) -> TaskBurnRateRead:
    """Derive burn-rate fields from a fully-loaded Task ORM object."""
    total = round(sum(ts.hours_logged for ts in task.timesheets), 2)
    pct   = round((total / task.quantity * 100) if task.quantity else 0.0, 1)
    # Warning only fires when the task is still in progress (AC 3)
    warning = pct >= 80 and task.status != TaskStatus.done
    return TaskBurnRateRead(
        task_id=task.id,
        task_name=task.name,
        task_status=task.status,
        quantity=task.quantity,
        total_hours_logged=total,
        remaining_hours=round(max(0.0, task.quantity - total), 2),
        burn_pct=pct,
        burn_warning=warning,
    )


# -- Public service functions -------------------------------------------------

def get_task_burn_rate(session: Session, task_id: int) -> TaskBurnRateRead | None:
    """Return burn metrics for a single Task, or None if not found."""
    task = session.get(Task, task_id)
    if task is None:
        return None
    return _compute_task_metrics(task)


def get_project_burn_rate(
    session: Session,
    project_id: int,
) -> ProjectBurnRateRead | None:
    """Return aggregated burn metrics for a Project and all its accepted Tasks.

    Only Tasks belonging to *accepted* Quotes are included; draft/sent/cancelled
    quotes are excluded because their Tasks cannot yet log time.
    Returns None when the Project ID does not exist.
    """
    project = session.get(Project, project_id)
    if project is None:
        return None

    stmt = (
        select(Task)
        .join(Quote, Task.quote_id == Quote.id)
        .where(Quote.project_id == project_id)
        .where(Quote.status == QuoteStatus.accepted)
        .order_by(Task.status.asc(), Task.name.asc())
    )
    tasks = session.exec(stmt).all()

    task_reads = [_compute_task_metrics(t) for t in tasks]

    total_qty = sum(t.quantity             for t in task_reads)
    total_hrs = sum(t.total_hours_logged   for t in task_reads)
    remaining = round(max(0.0, total_qty - total_hrs), 2)
    overall   = round((total_hrs / total_qty * 100) if total_qty else 0.0, 1)

    return ProjectBurnRateRead(
        project_id=project.id,
        project_name=project.name,
        project_status=project.status,
        total_quantity=round(total_qty, 2),
        total_hours_logged=round(total_hrs, 2),
        remaining_hours=remaining,
        overall_burn_pct=overall,
        burn_warning=overall >= 80,
        task_count=len(task_reads),
        tasks=task_reads,
    )


def get_all_projects_burn_rate(session: Session) -> list[ProjectBurnRateRead]:
    """Return burn metrics for every Project in the system (sorted by name).

    Projects with no accepted-quote Tasks still appear so PMs see the full
    project roster (overall_burn_pct will be 0 for those entries).
    """
    projects = session.exec(select(Project).order_by(Project.name)).all()
    results: list[ProjectBurnRateRead] = []
    for project in projects:
        data = get_project_burn_rate(session, project.id)
        if data is not None:
            results.append(data)
    return results
