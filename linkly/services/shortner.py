"""
This module contains the service level logic for the api.
"""

from datetime import datetime, timezone

import httpx
import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from fastapi_cache.decorator import cache
from motor.motor_asyncio import AsyncIOMotorDatabase

from linkly.database import get_db
from linkly.settings import settings
from linkly.utils.dtype import PyObjectId
from linkly.utils.encode_url import ShortIdGenerator

redis_client = redis.from_url(settings.redis_url, ssl=True)


async def shorten_url(
    original_url: str,
    db_cm: AsyncIOMotorDatabase,
    user_id: PyObjectId | str | None = None,  # user_id can be None now
    expiry: int | None = None,
) -> str:
    try:
        short_id = ShortIdGenerator.generate()[:5]
        short_url = settings.LOCAL_HOST + f"/{short_id}"
        created_at = int(datetime.utcnow().timestamp())

        url_doc = {
            "original_url": original_url,
            "short_id": short_id,
            "short_url": short_url,
            "user_id": PyObjectId(user_id),
            "created_at": created_at,
            "expiry": expiry,
        }

        if user_id:
            if isinstance(user_id, str):
                user_id = PyObjectId(user_id)
            url_doc["user_id"] = user_id  # only add if available

        await db_cm.urls.insert_one(url_doc)

        if expiry:
            await redis_client.set(f"expire:{short_id}", "1", ex=expiry)

        return short_url
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@cache(expire=180)
async def resolves_url(short_url: str, db_cm):
    """
    Accept the short url and return the original url
    """
    try:
        url_doc = await db_cm.urls.find_one({"short_url": short_url})
        if not url_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"{short_url} doenot exist in system"},
            )
        return url_doc["original_url"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# TODO: somethiing is off need to rewrite whole anaytics logic
async def url_analytics(short_url: str, request: Request, db_cm):
    header = request.headers.get("user-agent", "unknown")
    user_ip = request.client.host
    if user_ip == "127.0.0.1":
        user_ip = "8.8.8.8"

    fingerprint = f"{user_ip}{header}".lower().strip()

    location = None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(settings.IP_DETAILS_URL + f"/{user_ip}")
            if r.status_code == 200:
                data = r.json()
                city = data.get("city", "")
                country = data.get("country", "")
                location = ", ".join(filter(None, [city, country])) or None
    except Exception:
        location = None

    utm_source = request.query_params.get("utm_source")
    utm_medium = request.query_params.get("utm_medium")
    utm_campaign = request.query_params.get("utm_campaign")

    click_info = {
        "user_agent": header,
        "ip": user_ip,
        "timestamp": datetime.now(timezone.utc),
        "location": location,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
    }

    doc = await db_cm.url_analytics.find_one({"short_id": short_url})

    if not doc:
        await db_cm.url_analytics.insert_one(
            {
                "short_id": short_url,
                "clicks": 1,
                "finger_print": [fingerprint],
                "click_details": [click_info],
            }
        )
    else:
        if fingerprint not in (doc.get("finger_print") or []):
            await db_cm.url_analytics.update_one(
                {"short_id": short_url},
                {
                    "$inc": {"clicks": 1},
                    "$addToSet": {"finger_print": fingerprint},
                    "$push": {"click_details": click_info},
                },
            )
        else:
            pass


async def get_url_analytics(
    short_url: str,
    db_cm,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
):
    analytics_doc = await db_cm.url_analytics.find_one({"short_id": short_url})

    if not analytics_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics data not found for this short URL",
        )

    filtered_clicks = []
    for entry in analytics_doc.get("click_details", []):
        if utm_source and entry.get("utm_source") != utm_source:
            continue
        if utm_medium and entry.get("utm_medium") != utm_medium:
            continue
        if utm_campaign and entry.get("utm_campaign") != utm_campaign:
            continue
        filtered_clicks.append(entry)

    analytics_doc["_id"] = str(analytics_doc["_id"])
    for entry in filtered_clicks:
        entry["timestamp"] = entry["timestamp"].isoformat()

    analytics_doc["click_details"] = filtered_clicks
    analytics_doc["clicks"] = len(filtered_clicks)

    return analytics_doc


async def delete_url(short_url: str, db_cm):
    is_valid = await db_cm.urls.find_one({"short_url": short_url})
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Url not found"
        )
    result = await db_cm.urls.delete_one({"short_url": short_url})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )
    return {"message": "Url data successfully erased"}
