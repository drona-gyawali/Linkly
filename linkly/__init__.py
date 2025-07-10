from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield


from linkly.routes import shortner, auth

app = FastAPI(lifespan=lifespan)
app.include_router(shortner.router)
app.include_router(auth.router)
