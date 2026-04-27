from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.schemas.learnflow import UserProfileOut
from app.schemas.user import UserOut
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserProfileOut)
async def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    return await user_service.get_profile(current_user["id"])


@router.get("/", response_model=list[UserOut])
async def get_all_users(_: dict = Depends(require_role(UserRole.ADMIN))) -> list[dict]:
    return await user_service.list_users()


@router.delete("/{user_id}")
async def delete_user(user_id: str, _: dict = Depends(require_role(UserRole.ADMIN))) -> dict:
    return await user_service.delete_user(user_id)
