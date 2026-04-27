import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    db = AsyncIOMotorClient('mongodb://localhost:27017')['lms_db']
    user = await db.users.find_one({})
    if not user: return
    user_id = str(user["_id"])
    
    tasks = await db.tasks.find({"user_id": user_id}).to_list(None)
    for t in tasks:
        print(f"Task: {t.get('title')}, Status: {t.get('status')}, Deadline: {t.get('deadline_date')} / {t.get('deadline')}")

asyncio.run(run())
