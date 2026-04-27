from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


def get_database() -> AsyncIOMotorDatabase | None:
    """Always call this instead of `from app.db.mongodb import database` (stale None after connect)."""
    return database


async def connect_to_mongo() -> None:
    global client, database
    client = AsyncIOMotorClient(settings.mongodb_uri)
    database = client[settings.mongodb_db]


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
        client = None
