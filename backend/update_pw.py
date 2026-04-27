import asyncio
from app.db.mongodb import connect_to_mongo, get_database
from app.core.security import get_password_hash

async def main():
    await connect_to_mongo()
    db = get_database()
    pw = get_password_hash('learnflow123')
    await db.users.update_one({'email': 'mdsuhail63831@gmail.com'}, {'$set': {'hashed_password': pw}})
    print('Password updated!')

asyncio.run(main())
