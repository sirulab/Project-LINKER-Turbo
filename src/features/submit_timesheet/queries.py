"""Feature: submit_timesheet — reusable DB query helpers."""

from sqlmodel import Session, select

from src.models import Project, ProjectStatus, Quote, QuoteStatus, Task, TaskStatus


def get_open_tasks(session: Session) -> list[dict]:
    """Return all non-done tasks that belong to an accepted quote in an active project.

    Each entry is a dict with:
      task          - Task ORM object
      project_name  - str
      quote_number  - str
      total_hours   - float (sum of all timesheets on this task)
      burn_pct      - float (0–100+)
      burn_warning  - bool  (True when burn_pct >= 80)
    """
    stmt = (
        select(Task, Quote, Project)
        .join(Quote, Task.quote_id == Quote.id)
        .join(Project, Quote.project_id == Project.id)
        .where(Quote.status == QuoteStatus.accepted)
        .where(Project.status == ProjectStatus.active)
        .where(Task.status != TaskStatus.done)
        .order_by(Task.status.asc(), Task.name.asc())
    )
    rows = session.exec(stmt).all()

    results: list[dict] = []
    for task, quote, project in rows:
        total_hours = sum(ts.hours_logged for ts in task.timesheets)
        burn_pct = (total_hours / task.quantity * 100) if task.quantity else 0.0
        results.append(
            {
                "task": task,
                "project_name": project.name,
                "quote_number": quote.quote_number,
                "total_hours": round(total_hours, 2),
                "burn_pct": round(burn_pct, 1),
                "burn_warning": burn_pct >= 80,
            }
        )
    return results
