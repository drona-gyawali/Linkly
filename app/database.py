from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.settings import MONGODB_URI, DB_NAME
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
client = AsyncIOMotorClient(MONGODB_URI)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase | None]:
    try:
        db = client[DB_NAME]
        yield db
    finally:
        # yo motor use garda teardown logic chaina tarapani space xa hai: reason future proof.
        pass

# redis use garda we need serilaize data so making sync instance
def get_db_instance() -> AsyncIOMotorDatabase:
    return client[DB_NAME]