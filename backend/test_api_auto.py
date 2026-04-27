import asyncio
import os
import sys
import requests

sys.path.insert(0, r"E:\LM")
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "lms_db"

from app.db import mongodb
from app.services.auth_service import create_access_token

async def run():
    await mongodb.connect_to_mongo()
    db = mongodb.get_database()
    user = await db.users.find_one({})
    if not user: return
    user_id = str(user["_id"])
    
    token = create_access_token({"sub": user_id})
    day = "2026-04-26"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"http://localhost:8000/api/learnflow/planner/auto-schedule?day={day}", headers=headers)
    print("Status:", resp.status_code)
    if resp.status_code != 200:
        print("Error:", resp.text)
    else:
        blocks = resp.json().get("blocks", [])
        for b in blocks:
            print(f"[{b['time']}] {b['title']}")

asyncio.run(run())
