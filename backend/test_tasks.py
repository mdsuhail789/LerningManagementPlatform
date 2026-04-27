import asyncio
from app.db.mongodb import connect_to_mongo, get_database
from app.services.task_service import get_user_tasks

async def main():
    await connect_to_mongo()
    db = get_database()
    
    alex = await db.users.find_one({"email": "alex@learnflow.demo"})
    if not alex:
        print("Alex not found")
        return
    alex_id = str(alex["_id"])
    
    try:
        tasks = await get_user_tasks(alex_id)
        print("Success!", tasks)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
