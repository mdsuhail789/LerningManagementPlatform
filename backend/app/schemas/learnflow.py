from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class KPICard(BaseModel):
    label: str
    value: str
    sublabel: str | None = None
    icon: str | None = None
    variant: Literal["default", "primary"] = "default"


class CourseProgressRow(BaseModel):
    course_id: str
    title: str
    progress_percent: float
    theme: Literal["blue", "purple", "green", "orange", "teal"]


class TodayTaskItem(BaseModel):
    id: str
    kind: Literal["watch", "quiz", "assignment"]
    title: str
    subtitle: str | None = None
    status: Literal["completed", "in_progress", "due_tonight"]
    accent: Literal["blue", "green", "orange"]


class DeadlineItem(BaseModel):
    id: str
    title: str
    urgency_label: str
    urgency: Literal["today", "soon", "later"]


class LearnFlowDashboardResponse(BaseModel):
    greeting_name: str
    header_date: str
    task_summary: str
    kpis: list[KPICard]
    course_progress: list[CourseProgressRow]
    today_plan: list[TodayTaskItem]
    deadlines: list[DeadlineItem]
    weekly_hours: list[float]
    weekly_hours_label: str


class AnalyticsKPI(BaseModel):
    label: str
    value: str
    badge: str
    badge_tone: Literal["success", "warning", "info", "neutral"]


class MonthlyBar(BaseModel):
    month: str
    hours: float
    highlight: bool = False


class SubjectRow(BaseModel):
    name: str
    percent: float
    theme: Literal["blue", "purple", "green", "orange", "teal", "neutral"]


class PerformanceRow(BaseModel):
    course: str
    last_score: str
    score_tone: Literal["success", "warning", "danger", "neutral", "info"]
    progress_percent: float
    progress_theme: Literal["blue", "purple", "green", "orange", "teal", "neutral"]
    status: str
    status_tone: Literal["success", "warning", "neutral", "info"]
    trend: str


class LearnFlowAnalyticsResponse(BaseModel):
    period: Literal["month", "quarter", "all"]
    kpis: list[AnalyticsKPI]
    monthly_hours: list[MonthlyBar]
    subjects: list[SubjectRow]
    performance: list[PerformanceRow]


class CalendarDayCell(BaseModel):
    day: int
    is_current_month: bool
    is_today: bool
    is_deadline: bool


class PlannerCalendar(BaseModel):
    title: str
    weekday_labels: list[str] = Field(default_factory=list)
    days: list[CalendarDayCell]


class PlannerBlock(BaseModel):
    id: str | None = None
    time: str
    title: str
    subtitle: str
    duration_minutes: int | None = None
    duration_label: str | None = None
    status: Literal["done", "now", "pending", "scheduled"]


class LearnFlowPlannerResponse(BaseModel):
    view: Literal["day", "week", "month"] = "day"
    calendar_title: str
    calendar_weekday_labels: list[str] = Field(default_factory=list)
    calendar_days: list[CalendarDayCell]
    # New, simplified shape for clients: { calendar: { title, weekday_labels, days } }
    calendar: PlannerCalendar | None = None
    ai_recommendation: str
    timeline_title: str
    timeline_subtitle: str
    blocks: list[PlannerBlock]


class PlannerBlocksSave(BaseModel):
    day: date
    blocks: list[PlannerBlock]


class LearnFlowCourseCard(BaseModel):
    id: str
    title: str
    category: str
    category_theme: Literal["blue", "purple", "green", "teal", "orange"]
    image_url: str
    author: str
    module_count: int
    certificate_eligible: bool
    hours_remaining_label: str | None
    progress_percent: float
    cta_theme: Literal["blue", "purple", "green", "teal", "orange"]
    status: str
    cta_label: str = "Continue Learning"
    youtube_url: str | None = None
    learner_completed_count: int = 0
    learner_in_progress_count: int = 0
    learner_completed_names: list[str] = Field(default_factory=list)
    learner_in_progress_names: list[str] = Field(default_factory=list)


class LearnFlowCoursesResponse(BaseModel):
    summary: str
    courses: list[LearnFlowCourseCard]


class UserProfileOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: str | None = None
    tier_label: str | None = None


class SearchTaskItem(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    course_name: str | None
    deadline_label: str | None


class LearnFlowSearchResponse(BaseModel):
    courses: list[LearnFlowCourseCard]
    tasks: list[SearchTaskItem]


class NotificationItem(BaseModel):
    id: str
    title: str
    message: str
    type: Literal["alert", "warning", "success", "info"]
    timestamp: str | None


class LearnFlowNotificationsResponse(BaseModel):
    notifications: list[NotificationItem]
    unread_count: int


class CourseEnrollCreate(BaseModel):
    title: str = Field(..., max_length=150)
    category: str = Field(..., max_length=100)
    author: str = Field(..., max_length=150)
    youtube_url: str = Field(..., min_length=1, max_length=2000)


class CourseWatchProgressIn(BaseModel):
    seconds_watched: int = Field(default=15, ge=1, le=3600)
    current_seconds: int | None = Field(default=None, ge=0, le=86400)
    duration_seconds: int | None = Field(default=None, ge=1, le=86400)


class CourseWatchProgressOut(BaseModel):
    progress_percent: float
    status: Literal["in_progress", "completed"]
    resume_seconds: int = 0


class LearnFlowCourseDetailResponse(BaseModel):
    id: str
    title: str
    category: str
    author: str
    image_url: str
    module_count: int
    certificate_eligible: bool
    progress_percent: float
    status: Literal["in_progress", "completed"]
    youtube_url: str | None = None
    resume_seconds: int = 0

