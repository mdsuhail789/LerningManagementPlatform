from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.post("/", response_model=CourseOut)
async def create_course(payload: CourseCreate, current_user: dict = Depends(require_role(UserRole.ADMIN))) -> dict:
    return await course_service.create_course(current_user["id"], payload)


@router.get("/", response_model=list[CourseOut])
async def list_courses(current_user: dict = Depends(get_current_user)) -> list[dict]:
    if current_user["role"] == UserRole.ADMIN.value:
        return await course_service.get_all_courses()
    return await course_service.get_user_courses(current_user["id"])


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: str, payload: CourseUpdate, current_user: dict = Depends(get_current_user)
) -> dict:
    return await course_service.update_course(
        course_id=course_id,
        owner_id=current_user["id"],
        payload=payload,
        is_admin=current_user["role"] == UserRole.ADMIN.value,
    )


@router.delete("/{course_id}")
async def delete_course(course_id: str, current_user: dict = Depends(require_role(UserRole.ADMIN))) -> dict:
    return await course_service.delete_course(
        course_id=course_id,
        owner_id=current_user["id"],
        is_admin=True,
    )


@router.get("/{course_id}/progress")
async def get_course_progress(course_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    return await course_service.course_progress(
        course_id=course_id,
        owner_id=current_user["id"],
        is_admin=current_user["role"] == UserRole.ADMIN.value,
    )
