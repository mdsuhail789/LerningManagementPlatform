from datetime import datetime, timezone

from fastapi import HTTPException

from app.db.mongodb import get_database
from app.schemas.task import TaskCreate, TaskStatus, TaskUpdate
from app.services.common import to_object_id


def _serialize_task(doc: dict) -> dict:
    from datetime import datetime, timezone
    
    # Ensure deadline has zero time for Pydantic date validation
    fallback_dl = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    
    return {
        "id": str(doc["_id"]),
        "course_id": doc.get("course_id", ""),
        "user_id": doc.get("user_id", ""),
        "title": doc.get("title", "Untitled"),
        "description": doc.get("description", ""),
        "deadline": doc.get("deadline") or fallback_dl,
        "deadline_date": doc.get("deadline_date"),
        "duration_minutes": doc.get("duration_minutes"),
        "status": doc.get("status", "pending"),
        "video_url": doc.get("video_url") or "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "created_at": doc.get("created_at") or datetime.now(timezone.utc),
    }


async def create_task(course_id: str, user_id: str, payload: TaskCreate) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    course = await db.courses.find_one({"_id": to_object_id(course_id, "course_id")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    is_owner = course.get("owner_id") == user_id
    if not is_owner:
        # Learners can add their own tasks for enrolled/admin-published courses.
        has_progress = (
            await db.course_progress.count_documents({"course_id": course_id, "user_id": user_id}, limit=1)
        ) > 0
        owner_user = None
        owner_id = course.get("owner_id")
        if owner_id:
            owner_user = await db.users.find_one({"_id": to_object_id(owner_id, "owner_id")}, {"role": 1})
        owner_is_admin = str((owner_user or {}).get("role", "")).strip().lower() == "admin"

        if not has_progress and not owner_is_admin:
            raise HTTPException(status_code=403, detail="Not allowed to add tasks to this course")

    vid = payload.video_url
    video_str = str(vid) if vid is not None else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    dl = payload.deadline
    if type(dl) is not datetime:
        dl = datetime.combine(dl, datetime.min.time(), tzinfo=timezone.utc)
        
    doc = {
        "course_id": course_id,
        "user_id": user_id,
        "title": payload.title,
        "description": payload.description,
        "deadline": dl,
        # Store a timezone-safe date-only field for filtering (YYYY-MM-DD).
        # This avoids "wrong day" issues when comparing datetimes across timezones.
        "deadline_date": dl.date().isoformat(),
        "duration_minutes": payload.duration_minutes,
        "status": payload.status.value,
        "video_url": video_str,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.tasks.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_task(doc)


async def get_user_tasks(user_id: str) -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    tasks = await db.tasks.find({"user_id": user_id}).to_list(length=None)
    return [_serialize_task(t) for t in tasks]


async def get_all_tasks() -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    tasks = await db.tasks.find({}).to_list(length=None)
    return [_serialize_task(t) for t in tasks]


async def update_task(task_id: str, user_id: str, payload: TaskUpdate, is_admin: bool) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    task_obj_id = to_object_id(task_id, "task_id")
    task = await db.tasks.find_one({"_id": task_obj_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not is_admin and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this task")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "video_url" in updates:
        updates["video_url"] = str(updates["video_url"])
    if "status" in updates and hasattr(updates["status"], "value"):
        updates["status"] = updates["status"].value
    if "deadline" in updates and type(updates["deadline"]) is not datetime:
        updates["deadline"] = datetime.combine(updates["deadline"], datetime.min.time(), tzinfo=timezone.utc)
    if "deadline" in updates and isinstance(updates["deadline"], datetime):
        updates["deadline_date"] = updates["deadline"].date().isoformat()

    # If a task is marked completed, delete it from the database (LearnFlow behavior).
    # NOTE: We keep completed tasks for planner history ("Done" status in UI).
    # Use DELETE endpoint if you want to remove it permanently.

    if updates:
        await db.tasks.update_one({"_id": task_obj_id}, {"$set": updates})
        task.update(updates)

    return _serialize_task(task)


async def delete_task(task_id: str, user_id: str, is_admin: bool) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    task_obj_id = to_object_id(task_id, "task_id")
    task = await db.tasks.find_one({"_id": task_obj_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not is_admin and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this task")

    await db.tasks.delete_one({"_id": task_obj_id})
    return {"message": "Task deleted successfully"}
