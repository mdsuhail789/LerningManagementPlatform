import sys
import os
import asyncio
from datetime import date
from motor.motor_asyncio import AsyncIOMotorClient

# Setup path and env
sys.path.insert(0, r"E:\LM")
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "lms_db"

from app.db import mongodb
from app.services import learnflow_service

async def test_ai():
    # Setup DB connection
    await mongodb.connect_to_mongo()
    db = mongodb.get_database()
    
    # Get a user
    user = await db.users.find_one({})
    if not user:
        print("No users found.")
        return
        
    user_id = str(user["_id"])
    print(f"Testing AI with user {user_id} ({user.get('email')})")
    
    # Call apply_ai_recommendation
    print("Calling apply_ai_recommendation...")
    try:
        res = await learnflow_service.apply_ai_recommendation(user_id, date.today())
        print("\n--- AI RECOMMENDATION ---")
        print(res.get("ai_recommendation"))
        
        blocks = res.get("blocks", [])
        print(f"\n--- SCHEDULE BLOCKS ({len(blocks)}) ---")
        for b in blocks:
            print(f"[{b.get('time')}] {b.get('title')} ({b.get('status')})")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
    finally:
        await mongodb.close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_ai())
