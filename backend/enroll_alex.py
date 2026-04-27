import asyncio
from app.db.mongodb import connect_to_mongo, get_database
from bson import ObjectId

async def main():
    await connect_to_mongo()
    db = get_database()
    
    # 1. Get Learner (alex)
    alex = await db.users.find_one({"email": "alex@learnflow.demo"})
    if not alex:
        print("Alex not found")
        return
    alex_id = str(alex["_id"])
    
    # 2. Get Course (Python)
    course = await db.courses.find_one({"title": "Python"})
    if not course:
        print("Course not found")
        return
    course_id = str(course["_id"])
    
    # 3. Add course progress to Alex
    await db.course_progress.update_one(
        {"user_id": alex_id, "course_id": course_id},
        {"$set": {"progress_percent": 25, "last_accessed": "2026-04-26T00:00:00Z"}},
        upsert=True
    )
    
    # 4. Add a test task for Alex in Python course
    await db.tasks.update_one(
        {"user_id": alex_id, "course_id": course_id, "title": "Intro to Python Quiz"},
        {"$set": {
            "title": "Intro to Python Quiz",
            "description": "Basic variables and types",
            "status": "pending",
            "duration_minutes": 30,
            "deadline_date": "2026-04-28"
        }},
        upsert=True
    )
    
    print("Successfully enrolled alex@learnflow.demo into the Python course!")

asyncio.run(main())
