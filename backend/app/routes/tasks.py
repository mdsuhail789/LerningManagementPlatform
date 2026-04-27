from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import UserRole
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/course/{course_id}", response_model=TaskOut)
async def create_task(
    course_id: str, payload: TaskCreate, current_user: dict = Depends(get_current_user)
) -> dict:
    return await task_service.create_task(course_id=course_id, user_id=current_user["id"], payload=payload)


@router.get("/", response_model=list[TaskOut])
async def list_tasks(current_user: dict = Depends(get_current_user)) -> list[dict]:
    if current_user["role"] == UserRole.ADMIN.value:
        return await task_service.get_all_tasks()
    return await task_service.get_user_tasks(current_user["id"])


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, payload: TaskUpdate, current_user: dict = Depends(get_current_user)) -> dict:
    return await task_service.update_task(
        task_id=task_id,
        user_id=current_user["id"],
        payload=payload,
        is_admin=current_user["role"] == UserRole.ADMIN.value,
    )


@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    return await task_service.delete_task(
        task_id=task_id,
        user_id=current_user["id"],
        is_admin=current_user["role"] == UserRole.ADMIN.value,
    )
