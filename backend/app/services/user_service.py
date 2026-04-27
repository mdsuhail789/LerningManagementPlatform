from fastapi import HTTPException

from app.db.mongodb import get_database
from app.services.common import to_object_id


def _serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "full_name": doc["full_name"],
        "role": doc["role"],
    }


async def get_profile(user_id: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    user = await db.users.find_one({"_id": to_object_id(user_id, "user_id")})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "avatar_url": user.get("avatar_url"),
        "tier_label": user.get("tier_label"),
    }


async def list_users() -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    users = await db.users.find({}, {"password_hash": 0}).to_list(length=None)
    return [_serialize_user(u) for u in users]


async def delete_user(user_id: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    user_obj_id = to_object_id(user_id, "user_id")

    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    course_ids = [
        c["_id"] for c in await db.courses.find({"owner_id": user_id}).to_list(length=None)
    ]
    if course_ids:
        await db.tasks.delete_many({"course_id": {"$in": [str(cid) for cid in course_ids]}})
        await db.courses.delete_many({"_id": {"$in": course_ids}})

    await db.tasks.delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": user_obj_id})

    return {"message": "User deleted successfully"}
