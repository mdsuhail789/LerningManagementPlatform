import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    db = AsyncIOMotorClient('mongodb://localhost:27017')['lms_db']
    t = await db.tasks.find_one({'title': 'React focused study'}, sort=[('created_at', -1)])
    if t:
        print(t.get('description'))
    else:
        print('Not found')

asyncio.run(run())
