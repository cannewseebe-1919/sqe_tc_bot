import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="creator")


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(500))
    code: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    source_type: Mapped[str] = mapped_column(String(20))  # "chat" | "file_upload"
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | confirmed | pushed

    creator: Mapped["User"] = relationship(back_populates="test_cases")
    git_info: Mapped["GitInfo | None"] = relationship(back_populates="test_case", uselist=False)
    executions: Mapped[list["Execution"]] = relationship(back_populates="test_case")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    test_case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("test_cases.id"), nullable=True)
    device_id: Mapped[str] = mapped_column(String(255))
    requested_by: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="QUEUED")  # QUEUED|RUNNING|COMPLETED|FAILED|ABORTED
    queue_position: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    total_duration_sec: Mapped[float | None] = mapped_column(Float)

    test_case: Mapped["TestCase | None"] = relationship(back_populates="executions")
    steps: Mapped[list["ExecutionStep"]] = relationship(back_populates="execution")


class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"))
    step_name: Mapped[str] = mapped_column(String(255))
    step_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))  # PASSED | FAILED | SKIPPED
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    screenshot_path: Mapped[str | None] = mapped_column(String(500))
    log: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(50))

    execution: Mapped["Execution"] = relationship(back_populates="steps")


class GitInfo(Base):
    __tablename__ = "git_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_cases.id"), unique=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    branch: Mapped[str] = mapped_column(String(255))
    commit_message: Mapped[str] = mapped_column(Text)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime)
    pushed_by: Mapped[str] = mapped_column(String(255))

    test_case: Mapped["TestCase"] = relationship(back_populates="git_info")
