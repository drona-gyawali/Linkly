from fastapi import FastAPI
from fastapi_cache2 import FastAPICache
from fastapi_cache2.backends.redis import RedisBackend
import aioredis

app = FastAPI()

async def init_redis_cache():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.on_event("startup")
async def startup():
    await init_redis_cache()
