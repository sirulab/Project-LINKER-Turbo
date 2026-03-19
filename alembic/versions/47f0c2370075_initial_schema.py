"""initial schema

Revision ID: 47f0c2370075
Revises:
Create Date: 2026-03-19 13:05:20.050941

Hand-written initial migration.
Alembic autogenerate produced an empty diff because the SQLite dev database
already had all tables created by SQLModel.metadata.create_all().
This file creates the full schema from scratch so that a fresh PostgreSQL
database (e.g. Digital Ocean Managed PostgreSQL) is correctly initialised.
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '47f0c2370075'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── company ───────────────────────────────────────────────────────────────
    op.create_table(
        'company',
        sa.Column('id',      sa.Integer(),    nullable=False),
        sa.Column('name',    sqlmodel.AutoString(), nullable=False),
        sa.Column('tax_id',  sqlmodel.AutoString(), nullable=False),
        sa.Column('email',   sqlmodel.AutoString(), nullable=True),
        sa.Column('phone',   sqlmodel.AutoString(), nullable=True),
        sa.Column('address', sqlmodel.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_id'),
    )
    op.create_index('ix_company_name', 'company', ['name'], unique=False)

    # ── project ───────────────────────────────────────────────────────────────
    op.create_table(
        'project',
        sa.Column('id',          sa.Integer(),          nullable=False),
        sa.Column('name',        sqlmodel.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.AutoString(), nullable=True),
        sa.Column('status',      sqlmodel.AutoString(), nullable=False),
        sa.Column('start_date',  sa.Date(),             nullable=True),
        sa.Column('company_id',  sa.Integer(),          nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_name', 'project', ['name'], unique=False)

    # ── employee ──────────────────────────────────────────────────────────────
    op.create_table(
        'employee',
        sa.Column('id',          sa.Integer(),          nullable=False),
        sa.Column('name',        sqlmodel.AutoString(), nullable=False),
        sa.Column('email',       sqlmodel.AutoString(), nullable=False),
        sa.Column('role',        sqlmodel.AutoString(), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(),          nullable=False),
        sa.Column('is_active',   sa.Boolean(),          nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_employee_name',  'employee', ['name'],  unique=False)
    op.create_index('ix_employee_email', 'employee', ['email'], unique=True)

    # ── quote ─────────────────────────────────────────────────────────────────
    op.create_table(
        'quote',
        sa.Column('id',           sa.Integer(),          nullable=False),
        sa.Column('quote_number', sqlmodel.AutoString(), nullable=False),
        sa.Column('status',       sqlmodel.AutoString(), nullable=False),
        sa.Column('total_amount', sa.Numeric(),          nullable=False),
        sa.Column('valid_until',  sa.Date(),             nullable=True),
        sa.Column('created_at',   sa.DateTime(timezone=True), nullable=False),
        sa.Column('project_id',   sa.Integer(),          nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_number'),
    )
    op.create_index('ix_quote_quote_number', 'quote', ['quote_number'], unique=True)

    # ── task ──────────────────────────────────────────────────────────────────
    op.create_table(
        'task',
        sa.Column('id',          sa.Integer(),          nullable=False),
        sa.Column('name',        sqlmodel.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.AutoString(), nullable=True),
        sa.Column('quantity',    sa.Float(),            nullable=False),
        sa.Column('unit_price',  sa.Numeric(),          nullable=False),
        sa.Column('status',      sqlmodel.AutoString(), nullable=False),
        sa.Column('quote_id',    sa.Integer(),          nullable=True),
        sa.ForeignKeyConstraint(['quote_id'], ['quote.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_name', 'task', ['name'], unique=False)

    # ── timesheet ─────────────────────────────────────────────────────────────
    op.create_table(
        'timesheet',
        sa.Column('id',           sa.Integer(), nullable=False),
        sa.Column('hours_logged', sa.Float(),   nullable=False),
        sa.Column('date_logged',  sa.Date(),    nullable=False),
        sa.Column('description',  sqlmodel.AutoString(), nullable=True),
        sa.Column('employee_id',  sa.Integer(), nullable=True),
        sa.Column('task_id',      sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id']),
        sa.ForeignKeyConstraint(['task_id'],     ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_timesheet_employee_id', 'timesheet', ['employee_id'], unique=False)
    op.create_index('ix_timesheet_task_id',     'timesheet', ['task_id'],     unique=False)


def downgrade() -> None:
    op.drop_table('timesheet')
    op.drop_table('task')
    op.drop_table('quote')
    op.drop_table('employee')
    op.drop_table('project')
    op.drop_table('company')
