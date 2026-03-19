"""
Shared module: all SQLModel table definitions.

Defines 6 core tables corresponding to the Phase 02 domain model document:
  Company → Project → Quote → Task ← Timesheet → Employee

All enums, relationships, and business-rule constraints (soft-delete,
status machines) are captured here.  SQLModel.metadata.create_all() in
database.py discovers every table in this file automatically.

Financial fields (total_amount, unit_price, hourly_rate) use Python's
Decimal type for precision.  SQLite stores these as NUMERIC; switching to
PostgreSQL will use the native NUMERIC column without model changes.

── Auto-generated field convention ──────────────────────────────────────────
  id          Optional[int], primary_key=True, default=None
              → SQLite/PostgreSQL auto-increments on INSERT; never include in
                Create schemas so Swagger UI hides it.

  created_at  datetime, default_factory=lambda: datetime.now(timezone.utc)
              → Timezone-aware UTC timestamp set at INSERT time; never include
                in Create schemas.

  date_logged date, default_factory=date.today
              → Defaults to today but is surfaced in the Timesheet HTML form
                so the employee can correct it; intentionally kept in the form
                schema as a user-editable field.
─────────────────────────────────────────────────────────────────────────────
"""

import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


# ── Enums ─────────────────────────────────────────────────────────────────────
# Inheriting from `str` makes JSON serialisation and SQLite storage work
# without any extra encoder configuration.

class EmployeeRole(str, enum.Enum):
    """RBAC roles.  See Phase 02 §2 for permission details."""
    admin    = "admin"
    employee = "employee"


class ProjectStatus(str, enum.Enum):
    """
    Lifecycle of a Project.

    active    → completed : all work done; blocks new Timesheets under Tasks
    active    → archived  : hidden from day-to-day views; history still readable
    completed → archived  : long-term archival
    """
    active    = "active"
    completed = "completed"
    archived  = "archived"


class QuoteStatus(str, enum.Enum):
    """
    Lifecycle of a Quote.

    draft    → sent      : freeze Task amounts & quantities
    sent     → accepted  : side-effect — open Tasks for Timesheet submission
    sent     → cancelled : project not proceeding
    accepted → cancelled : contract revoked
    """
    draft     = "draft"
    sent      = "sent"
    accepted  = "accepted"
    cancelled = "cancelled"


class TaskStatus(str, enum.Enum):
    """
    Lifecycle of a Task.

    todo  → doing : first Timesheet submitted against this Task (auto-transition)
    doing → done  : employee marks complete; requires ≥1 Timesheet (enforced in router)
    """
    todo  = "todo"
    doing = "doing"
    done  = "done"


# ── Company ───────────────────────────────────────────────────────────────────

class Company(SQLModel, table=True):
    """客戶公司 — the contracting party for a project."""

    id:      Optional[int] = Field(default=None, primary_key=True)
    name:    str            = Field(index=True)
    tax_id:  str            = Field(unique=True, description="統一編號")
    email:   Optional[str]  = Field(default=None)
    phone:   Optional[str]  = Field(default=None)
    address: Optional[str]  = Field(default=None)

    # ── Relationships ──────────────────────────────────────────────────────
    projects: list["Project"] = Relationship(back_populates="company")


# ── Project ───────────────────────────────────────────────────────────────────

class Project(SQLModel, table=True):
    """專案 — top-level execution container owned by a Company."""

    id:          Optional[int]   = Field(default=None, primary_key=True)
    name:        str              = Field(index=True)
    description: Optional[str]   = Field(default=None)
    status:      ProjectStatus    = Field(default=ProjectStatus.active)
    start_date:  Optional[date]   = Field(default=None)

    # FK
    company_id:  Optional[int]   = Field(default=None, foreign_key="company.id")

    # ── Relationships ──────────────────────────────────────────────────────
    company: Optional[Company]   = Relationship(back_populates="projects")
    quotes:  list["Quote"]       = Relationship(back_populates="project")


# ── Quote ─────────────────────────────────────────────────────────────────────

class Quote(SQLModel, table=True):
    """報價單 — a priced proposal attached to a Project."""

    id:           Optional[int]  = Field(default=None, primary_key=True)
    quote_number: str             = Field(unique=True, index=True, description="e.g. QUO-2024-001")
    status:       QuoteStatus     = Field(default=QuoteStatus.draft)
    total_amount: Decimal         = Field(default=Decimal("0.00"), description="Sum of Task line amounts (NTD)")
    valid_until:  Optional[date]  = Field(default=None)
    created_at:   datetime        = Field(default_factory=lambda: datetime.now(timezone.utc))

    # FK
    project_id:   Optional[int]  = Field(default=None, foreign_key="project.id")

    # ── Relationships ──────────────────────────────────────────────────────
    project: Optional[Project]   = Relationship(back_populates="quotes")
    tasks:   list["Task"]        = Relationship(back_populates="quote")


# ── Task ──────────────────────────────────────────────────────────────────────

class Task(SQLModel, table=True):
    """任務 — a billable line item inside a Quote; the unit for Timesheet logging."""

    id:          Optional[int] = Field(default=None, primary_key=True)
    name:        str            = Field(index=True)
    description: Optional[str] = Field(default=None)

    # Estimated hours sold to the client (used for burn-rate calculation).
    # Burn-rate warning fires when Σ hours_logged ≥ quantity × 0.8.
    quantity:    float          = Field(description="Estimated hours (sold to client)")
    unit_price:  Decimal        = Field(description="Price per hour (NTD)")
    status:      TaskStatus     = Field(default=TaskStatus.todo)

    # FK
    quote_id:    Optional[int] = Field(default=None, foreign_key="quote.id")

    # ── Relationships ──────────────────────────────────────────────────────
    quote:      Optional[Quote]    = Relationship(back_populates="tasks")
    timesheets: list["Timesheet"]  = Relationship(back_populates="task")


# ── Employee ──────────────────────────────────────────────────────────────────

class Employee(SQLModel, table=True):
    """員工 — internal user (consultant or PM).

    Business rule: never DELETE a record.  Set is_active=False on departure
    so that historical Timesheet cost calculations remain intact.
    """

    id:          Optional[int]  = Field(default=None, primary_key=True)
    name:        str             = Field(index=True)
    email:       str             = Field(unique=True, index=True)
    role:        EmployeeRole    = Field(default=EmployeeRole.employee)

    # Internal cost rate — visible only to `admin` role in the UI.
    hourly_rate: Decimal         = Field(description="Internal cost per hour (NTD)")

    # Soft-delete flag — see business rule §5.3.
    is_active:   bool            = Field(default=True)

    # ── Relationships ──────────────────────────────────────────────────────
    timesheets: list["Timesheet"] = Relationship(back_populates="employee")


# ── Timesheet ─────────────────────────────────────────────────────────────────

class Timesheet(SQLModel, table=True):
    """工時表 — a single time-log entry by an Employee against a Task.

    Business rules:
    • Must be bound to exactly one Employee AND one Task (enforced by NOT NULL FKs).
    • Cannot be added when Task.quote.project.status is completed or archived.
    • Submitting the first entry auto-transitions Task.status → doing (router logic).
    """

    id:           Optional[int] = Field(default=None, primary_key=True)
    hours_logged: float          = Field(gt=0, description="Hours spent (must be > 0)")
    date_logged:  date           = Field(default_factory=date.today, description="Calendar date of the work; defaults to today")
    description:  Optional[str] = Field(default=None, description="Brief work summary")

    # FKs — intentionally non-nullable at the DB level via foreign_key + index.
    employee_id:  Optional[int] = Field(default=None, foreign_key="employee.id", index=True)
    task_id:      Optional[int] = Field(default=None, foreign_key="task.id",     index=True)

    # ── Relationships ──────────────────────────────────────────────────────
    employee: Optional[Employee] = Relationship(back_populates="timesheets")
    task:     Optional[Task]     = Relationship(back_populates="timesheets")
