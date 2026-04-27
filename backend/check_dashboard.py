import asyncio
import os
import sys
from bson import ObjectId

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.mongodb import connect_to_mongo, get_database, close_mongo_connection
from app.services.learnflow_service import dashboard

async def check():
    await connect_to_mongo()
    db = get_database()
    
    admin_user = await db.users.find_one({"email": "mdsuhail63831@gmail.com"})
    normal_user = await db.users.find_one({"email": "alex@learnflow.demo"})
    
    print(f"--- Testing Admin Dashboard ({admin_user['email']}) ---")
    try:
        admin_dash = await dashboard(str(admin_user["_id"]))
        print(f"KPIs: {[k['label'] + ': ' + str(k['value']) for k in admin_dash['kpis']]}")
        print(f"Courses in progress: {len(admin_dash['course_progress'])}")
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        
    print(f"\n--- Testing User Dashboard ({normal_user['email']}) ---")
    try:
        user_dash = await dashboard(str(normal_user["_id"]))
        print(f"KPIs: {[k['label'] + ': ' + str(k['value']) for k in user_dash['kpis']]}")
        print(f"Courses in progress: {len(user_dash['course_progress'])}")
    except Exception as e:
        print(f"User dashboard error: {e}")

    await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(check())
