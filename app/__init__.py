from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield

from app.routes import shortner
app = FastAPI(lifespan=lifespan)
app.include_router(shortner.router)
