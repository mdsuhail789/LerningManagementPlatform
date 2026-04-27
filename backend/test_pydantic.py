import asyncio
from datetime import date
import sys
import os

sys.path.insert(0, r"E:\LM")
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "lms_db"

from app.db import mongodb
from app.services import learnflow_service
from app.schemas.learnflow import LearnFlowPlannerResponse

async def run():
    await mongodb.connect_to_mongo()
    db = mongodb.get_database()
    user = await db.users.find_one({})
    if not user: return
    user_id = str(user["_id"])
    
    res = await learnflow_service.auto_schedule_day(user_id, date.today())
    try:
        LearnFlowPlannerResponse(**res)
        print("Pydantic validation PASSED")
    except Exception as e:
        print("Pydantic validation FAILED")
        print(e)

asyncio.run(run())
