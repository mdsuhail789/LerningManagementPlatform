from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.planner import PlannerResponse
from app.services import planner_service

router = APIRouter(prefix="/api/planner", tags=["Planner"])


@router.get("/daily", response_model=PlannerResponse)
async def get_daily_plan(current_user: dict = Depends(get_current_user)) -> dict:
    return await planner_service.generate_daily_plan(current_user["id"])
