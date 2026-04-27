import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import sys
import os

sys.path.insert(0, r"E:\LM\backend")
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "lms_db"

from app.db import mongodb
from app.services import learnflow_service

async def run():
    await mongodb.connect_to_mongo()
    db = mongodb.get_database()
    user = await db.users.find_one({})
    if not user: return
    user_id = str(user["_id"])
    
    res = await learnflow_service.auto_schedule_day(user_id, datetime.date.today())
    print("Auto-Schedule Response:")
    for b in res.get("blocks", []):
        print(f"[{b.get('time')}] {b.get('title')}")

asyncio.run(run())
