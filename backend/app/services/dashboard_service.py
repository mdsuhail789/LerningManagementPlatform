from fastapi import HTTPException

from app.db.mongodb import get_database
from app.schemas.task import TaskStatus


async def admin_dashboard() -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    total_users = await db.users.count_documents({})
    total_courses = await db.courses.count_documents({})
    total_tasks = await db.tasks.count_documents({})
    completed_tasks = await db.tasks.count_documents({"status": TaskStatus.COMPLETED.value})
    pending_tasks = await db.tasks.count_documents({"status": TaskStatus.PENDING.value})

    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
    }


async def user_dashboard(user_id: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    courses = await db.courses.find({"owner_id": user_id}).to_list(length=None)
    total_courses = len(courses)
    total_tasks = await db.tasks.count_documents({"user_id": user_id})
    completed_tasks = await db.tasks.count_documents(
        {"user_id": user_id, "status": TaskStatus.COMPLETED.value}
    )
    pending_tasks = await db.tasks.count_documents(
        {"user_id": user_id, "status": TaskStatus.PENDING.value}
    )
    overall_completion_percentage = (completed_tasks / total_tasks * 100.0) if total_tasks else 0.0

    course_progress = []
    for course in courses:
        course_id = str(course["_id"])
        course_task_count = await db.tasks.count_documents({"course_id": course_id})
        course_completed_count = await db.tasks.count_documents(
            {"course_id": course_id, "status": TaskStatus.COMPLETED.value}
        )
        percentage = (course_completed_count / course_task_count * 100.0) if course_task_count else 0.0
        course_progress.append(
            {
                "course_id": course_id,
                "title": course["title"],
                "completion_percentage": round(percentage, 2),
                "total_tasks": course_task_count,
                "completed_tasks": course_completed_count,
            }
        )

    return {
        "total_courses": total_courses,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overall_completion_percentage": round(overall_completion_percentage, 2),
        "course_progress": course_progress,
    }
