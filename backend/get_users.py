import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.mongodb import connect_to_mongo, get_database, close_mongo_connection

async def get_creds():
    await connect_to_mongo()
    db = get_database()
    users = await db.users.find({}).to_list(10)
    for u in users:
        print(f"Email: {u.get('email')}, Role: {u.get('role')}")
    await close_mongo_connection()

asyncio.run(get_creds())
