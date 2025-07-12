from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from linkly.settings import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = client[settings.DB_NAME]
    try:
        yield db
    finally:
        # yo motor use garda teardown logic chaina tarapani space xa hai: reason future proof.
        pass


# redis use garda we need serilaize data so making sync instance
def get_db_instance() -> AsyncIOMotorDatabase:
    return client[settings.DB_NAME]
