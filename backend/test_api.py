import asyncio
import httpx
from app.db.mongodb import connect_to_mongo, get_database
from app.core.security import create_access_token

async def main():
    await connect_to_mongo()
    db = get_database()
    
    alex = await db.users.find_one({"email": "alex@learnflow.demo"})
    if not alex:
        print("Alex not found")
        return
    
    token = create_access_token(
        data={"sub": str(alex["_id"]), "role": alex.get("role", "user")},
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:8000/api/tasks/", headers=headers)
        print("Status:", resp.status_code)
        print("Body:", resp.text)

asyncio.run(main())
