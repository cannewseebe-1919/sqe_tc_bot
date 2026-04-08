"""Initial tables: users, test_cases, executions, execution_steps, git_info

Revision ID: 001
Revises:
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "test_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("created_by", sa.String(255), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
    )

    op.create_table(
        "executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("test_case_id", sa.String(36), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("requested_by", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="QUEUED"),
        sa.Column("queue_position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("total_duration_sec", sa.Float, nullable=True),
    )

    op.create_table(
        "execution_steps",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("execution_id", sa.String(36), sa.ForeignKey("executions.id"), nullable=False),
        sa.Column("step_name", sa.String(255), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("duration_sec", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("screenshot_path", sa.String(500), nullable=True),
        sa.Column("log", sa.Text, nullable=True),
        sa.Column("error_type", sa.String(50), nullable=True),
    )

    op.create_table(
        "git_info",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("test_case_id", sa.String(36), sa.ForeignKey("test_cases.id"), unique=True, nullable=False),
        sa.Column("repo_url", sa.String(500), nullable=False),
        sa.Column("branch", sa.String(255), nullable=False),
        sa.Column("commit_message", sa.Text, nullable=False),
        sa.Column("pushed_at", sa.DateTime, nullable=True),
        sa.Column("pushed_by", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("git_info")
    op.drop_table("execution_steps")
    op.drop_table("executions")
    op.drop_table("test_cases")
    op.drop_table("users")
