"""Feature: analyze_burn_rate - response schemas.

Two read-only schemas are exposed:
  TaskBurnRateRead    - per-task burn metrics (AC 1 & 2)
  ProjectBurnRateRead - aggregated project-level metrics with nested tasks
"""

from pydantic import BaseModel

from src.models import ProjectStatus, TaskStatus


class TaskBurnRateRead(BaseModel):
    """Burn-rate metrics for a single Task (Story 1 AC 1-3)."""

    task_id:            int
    task_name:          str
    task_status:        TaskStatus

    # Quantities
    quantity:           float   # estimated hours sold to the client
    total_hours_logged: float   # sum of Timesheet.hours_logged
    remaining_hours:    float   # max(0, quantity - logged); capped at 0 when over-budget

    # Computed ratios
    burn_pct:           float   # (total_hours_logged / quantity) * 100; may exceed 100
    burn_warning:       bool    # True when burn_pct >= 80 AND task is not yet done

    model_config = {"from_attributes": True}


class ProjectBurnRateRead(BaseModel):
    """Aggregated burn-rate metrics for an entire Project (Story 1 AC 1-3)."""

    project_id:         int
    project_name:       str
    project_status:     ProjectStatus

    # Aggregated quantities across all accepted-quote Tasks
    total_quantity:     float   # sum of Task.quantity
    total_hours_logged: float   # sum of Timesheet.hours_logged
    remaining_hours:    float   # max(0, total_quantity - total_hours_logged)
    overall_burn_pct:   float   # (total_hours_logged / total_quantity) * 100
    burn_warning:       bool    # True when overall_burn_pct >= 80
    task_count:         int

    tasks:              list[TaskBurnRateRead]

    model_config = {"from_attributes": True}
