from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.schemas.dashboard import AdminDashboardResponse, UserDashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/user", response_model=UserDashboardResponse)
async def get_user_dashboard(current_user: dict = Depends(get_current_user)) -> dict:
    return await dashboard_service.user_dashboard(current_user["id"])


@router.get("/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard(_: dict = Depends(require_role(UserRole.ADMIN))) -> dict:
    return await dashboard_service.admin_dashboard()
