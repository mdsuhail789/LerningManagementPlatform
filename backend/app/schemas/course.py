from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str | None = Field(default=None, max_length=80)
    category_theme: Literal["blue", "purple", "green", "teal", "orange"] | None = None
    cta_theme: Literal["blue", "purple", "green", "teal", "orange"] | None = None
    image_url: str | None = Field(default=None, max_length=2000)
    author: str | None = Field(default=None, max_length=120)
    module_count: int | None = Field(default=None, ge=0)
    certificate_eligible: bool | None = None
    course_status: Literal["in_progress", "completed", "saved"] | None = None
    saved: bool | None = None
    hours_remaining_label: str | None = Field(default=None, max_length=80)
    progress_override: float | None = Field(default=None, ge=0, le=100)
    theme_color: Literal["blue", "purple", "green", "orange", "teal"] | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=80)
    category_theme: Literal["blue", "purple", "green", "teal", "orange"] | None = None
    cta_theme: Literal["blue", "purple", "green", "teal", "orange"] | None = None
    image_url: str | None = Field(default=None, max_length=2000)
    author: str | None = Field(default=None, max_length=120)
    module_count: int | None = Field(default=None, ge=0)
    certificate_eligible: bool | None = None
    course_status: Literal["in_progress", "completed", "saved"] | None = None
    saved: bool | None = None
    hours_remaining_label: str | None = Field(default=None, max_length=80)
    progress_override: float | None = Field(default=None, ge=0, le=100)
    theme_color: Literal["blue", "purple", "green", "orange", "teal"] | None = None


class CourseOut(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str
    created_at: datetime
    category: str | None = None
    category_theme: str | None = None
    cta_theme: str | None = None
    image_url: str | None = None
    author: str | None = None
    module_count: int | None = None
    certificate_eligible: bool | None = None
    course_status: str | None = None
    saved: bool | None = None
    hours_remaining_label: str | None = None
    progress_override: float | None = None
    theme_color: str | None = None
