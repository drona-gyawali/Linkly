from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from linkly.routes import auth, shortner


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shortner.router)
app.include_router(auth.router)
