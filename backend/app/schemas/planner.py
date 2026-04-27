from datetime import date

from pydantic import BaseModel


class DailyPlanItem(BaseModel):
    date: date
    tasks: list[dict]


class PlannerResponse(BaseModel):
    schedule: list[DailyPlanItem]
