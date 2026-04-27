from collections import defaultdict
from datetime import date, timedelta

from fastapi import HTTPException

from app.db.mongodb import get_database
from app.schemas.task import TaskStatus


async def generate_daily_plan(user_id: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    pending_tasks = await db.tasks.find(
        {"user_id": user_id, "status": TaskStatus.PENDING.value}
    ).to_list(length=None)

    today = date.today()
    pending_tasks.sort(key=lambda x: x["deadline"])
    schedule: dict[date, list[dict]] = defaultdict(list)

    for task in pending_tasks:
        task_deadline = task["deadline"]
        start_day = today
        if task_deadline < today:
            task_deadline = today

        candidate_days: list[date] = []
        current_day = start_day
        while current_day <= task_deadline:
            candidate_days.append(current_day)
            current_day += timedelta(days=1)

        if not candidate_days:
            candidate_days = [today]

        chosen_day = min(candidate_days, key=lambda day: len(schedule[day]))
        schedule[chosen_day].append(
            {
                "task_id": str(task["_id"]),
                "course_id": task["course_id"],
                "title": task["title"],
                "deadline": task["deadline"],
                "status": task["status"],
                "video_url": task["video_url"],
            }
        )

    ordered_schedule = [{"date": day, "tasks": tasks} for day, tasks in sorted(schedule.items())]
    return {"schedule": ordered_schedule}
