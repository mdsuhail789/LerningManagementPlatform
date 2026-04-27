from datetime import datetime, timezone

from fastapi import HTTPException

from app.db.mongodb import get_database
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.task import TaskStatus
from app.services.common import to_object_id


def _serialize_course(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "owner_id": doc["owner_id"],
        "title": doc["title"],
        "description": doc.get("description", ""),
        "created_at": doc["created_at"],
        "category": doc.get("category"),
        "category_theme": doc.get("category_theme"),
        "cta_theme": doc.get("cta_theme"),
        "image_url": doc.get("image_url"),
        "author": doc.get("author"),
        "module_count": doc.get("module_count"),
        "certificate_eligible": doc.get("certificate_eligible"),
        "course_status": doc.get("course_status"),
        "saved": doc.get("saved"),
        "hours_remaining_label": doc.get("hours_remaining_label"),
        "progress_override": doc.get("progress_override"),
        "theme_color": doc.get("theme_color"),
    }


async def create_course(owner_id: str, payload: CourseCreate) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    extra = payload.model_dump(exclude_unset=True, exclude={"title", "description"})
    doc = {
        "owner_id": owner_id,
        "title": payload.title,
        "description": payload.description,
        "created_at": datetime.now(timezone.utc),
        **{k: v for k, v in extra.items() if v is not None},
    }
    result = await db.courses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_course(doc)


async def get_user_courses(owner_id: str) -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    courses = await db.courses.find({"owner_id": owner_id}).to_list(length=None)
    return [_serialize_course(c) for c in courses]


async def get_all_courses() -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    courses = await db.courses.find({}).to_list(length=None)
    return [_serialize_course(c) for c in courses]


async def update_course(course_id: str, owner_id: str, payload: CourseUpdate, is_admin: bool) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    course_obj_id = to_object_id(course_id, "course_id")
    course = await db.courses.find_one({"_id": course_obj_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not is_admin and course["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this course")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.courses.update_one({"_id": course_obj_id}, {"$set": updates})
        course.update(updates)
    return _serialize_course(course)


async def delete_course(course_id: str, owner_id: str, is_admin: bool) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    course_obj_id = to_object_id(course_id, "course_id")
    course = await db.courses.find_one({"_id": course_obj_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not is_admin and course["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this course")

    await db.tasks.delete_many({"course_id": course_id})
    await db.courses.delete_one({"_id": course_obj_id})
    return {"message": "Course deleted successfully"}


async def course_progress(course_id: str, owner_id: str, is_admin: bool) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    course_obj_id = to_object_id(course_id, "course_id")
    course = await db.courses.find_one({"_id": course_obj_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not is_admin and course["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed to view this course")

    total_tasks = await db.tasks.count_documents({"course_id": course_id})
    completed_tasks = await db.tasks.count_documents(
        {"course_id": course_id, "status": TaskStatus.COMPLETED.value}
    )
    percentage = (completed_tasks / total_tasks * 100.0) if total_tasks else 0.0
    return {
        "course_id": course_id,
        "title": course["title"],
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": round(percentage, 2),
    }
