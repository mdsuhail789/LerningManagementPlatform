import asyncio
from app.db.mongodb import connect_to_mongo, get_database

async def main():
    await connect_to_mongo()
    db = get_database()
    
    # Delete the test task
    result = await db.tasks.delete_many({"title": "Intro to Python Quiz"})
    print(f"Deleted {result.deleted_count} tasks.")

asyncio.run(main())
