from datetime import date, datetime
from enum import Enum

from pydantic import AnyUrl, BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=3000)
    deadline: date
    duration_minutes: int | None = Field(default=None, ge=5, le=24 * 60)
    status: TaskStatus = TaskStatus.PENDING


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=3000)
    deadline: date | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=24 * 60)
    status: TaskStatus | None = None


class TaskOut(BaseModel):
    id: str
    course_id: str
    user_id: str
    title: str
    description: str
    deadline: date
    deadline_date: str | None = None
    duration_minutes: int | None = None
    status: TaskStatus
    created_at: datetime
