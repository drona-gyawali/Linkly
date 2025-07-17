import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware

from linkly.database import get_db_instance

# --- Routers ---
from linkly.routes import auth, shortner
from linkly.settings import settings


# --- Redis Key Expiry Listener ---
async def redis_key_expiry_listener(redis_client):
    await redis_client.config_set("notify-keyspace-events", "Ex")
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("__keyevent@0__:expired")

    db = get_db_instance()
    async for message in pubsub.listen():
        if message["type"] == "message":
            key = message["data"]
            if isinstance(key, bytes):
                key = key.decode()
            if key.startswith("expire:"):
                short_id = key.split(":")[1]
                await db.urls.delete_one({"short_id": short_id})
                print(f"[✔] Deleted expired link: {short_id}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = settings.redis_url.replace("redis://", "rediss://")
    redis_client = redis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    
    asyncio.create_task(redis_key_expiry_listener(redis_client))
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost",
    "https://drona-gyawali.github.io",
    "https://linkly-production.up.railway.app",
    "*",
]


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    same_site = "lax"
    # https_only=True    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(shortner.router)
