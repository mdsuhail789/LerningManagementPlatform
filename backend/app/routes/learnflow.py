from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.schemas.learnflow import (
    LearnFlowAnalyticsResponse,
    LearnFlowCoursesResponse,
    LearnFlowDashboardResponse,
    LearnFlowNotificationsResponse,
    LearnFlowPlannerResponse,
    LearnFlowSearchResponse,
    PlannerBlocksSave,
    CourseEnrollCreate,
    LearnFlowCourseDetailResponse,
    CourseWatchProgressIn,
    CourseWatchProgressOut,
)
from app.services import learnflow_service

router = APIRouter(prefix="/api/learnflow", tags=["LearnFlow"])


@router.get("/dashboard", response_model=LearnFlowDashboardResponse)
async def learnflow_dashboard(current_user: dict = Depends(get_current_user)) -> dict:
    return await learnflow_service.dashboard(current_user["id"])


@router.get("/analytics", response_model=LearnFlowAnalyticsResponse)
async def learnflow_analytics(
    period: str = Query("month", pattern="^(month|quarter|all)$"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.analytics(current_user["id"], period)


@router.get("/planner", response_model=LearnFlowPlannerResponse)
async def learnflow_planner(
    view: str = Query("day", pattern="^(day|week|month)$"),
    day: date | None = Query(None, description="Reference day for timeline and calendar month"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.planner(current_user["id"], view, day)


@router.put("/planner/blocks")
async def learnflow_planner_save_blocks(
    payload: PlannerBlocksSave,
    current_user: dict = Depends(get_current_user),
) -> dict:
    blocks = [b.model_dump() for b in payload.blocks]
    return await learnflow_service.save_planner_blocks(current_user["id"], payload.day, blocks)


@router.post("/planner/apply-recommendation")
async def learnflow_planner_apply_recommendation(
    day: date | None = Query(None, description="Generate schedule using AI recommendation"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.apply_ai_recommendation(current_user["id"], day)


@router.post("/planner/auto-schedule", response_model=LearnFlowPlannerResponse)
async def learnflow_planner_auto_schedule(
    day: date | None = Query(None, description="Auto-schedule tasks into time slots for a day"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.auto_schedule_day(current_user["id"], day)


@router.get("/courses", response_model=LearnFlowCoursesResponse)
async def learnflow_courses(
    status: str = Query("all", pattern="^(all|in_progress|completed)$"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.courses_catalog(current_user, status)


@router.get("/courses/{course_id}", response_model=LearnFlowCourseDetailResponse)
async def learnflow_course_detail(
    course_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.course_detail(current_user, course_id)


@router.get("/search", response_model=LearnFlowSearchResponse)
async def learnflow_search(
    q: str = Query("", description="Search query"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.global_search(current_user["id"], q)


@router.get("/notifications", response_model=LearnFlowNotificationsResponse)
async def learnflow_notifications(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.get_smart_notifications(current_user["id"])


@router.post("/courses")
async def learnflow_enroll_course(
    payload: CourseEnrollCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    return await learnflow_service.enroll_new_course(current_user["id"], payload.model_dump())


@router.post("/courses/{course_id}/watch-progress", response_model=CourseWatchProgressOut)
async def learnflow_course_watch_progress(
    course_id: str,
    payload: CourseWatchProgressIn,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return await learnflow_service.record_watch_progress(
        current_user,
        course_id,
        payload.seconds_watched,
        payload.current_seconds,
        payload.duration_seconds,
    )
