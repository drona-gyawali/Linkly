"""
This module contains the service level logic for the api.
"""

from datetime import datetime, timezone

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi_cache.decorator import cache
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.settings import IP_DETAILS_URL, LOCAL_HOST
from app.utils.encode_url import ShortIdGenerator


async def shorten_url(
    original_url: str, db_cm: AsyncIOMotorDatabase = Depends(get_db)
) -> str:
    """
    Take the long url as input and return working short url
    """
    try:
        async with db_cm as db:
            hash = ShortIdGenerator.generate()
            short_url = LOCAL_HOST + f"/{hash}"
            await db.urls.insert_one(
                {"original_url": original_url, "short_url": short_url}
            )
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


async def url_analytics(short_url: str, request: Request, db_cm):
    header = request.headers.get("user-agent", "unknown")
    user_ip = request.client.host
    if user_ip == "127.0.0.1":
        user_ip = "8.8.8.8"

    fingerprint = f"{user_ip}{header}".lower().strip()

    location = None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(IP_DETAILS_URL + f"/{user_ip}")
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
    async with db_cm as db:
        analytics_doc = await db.url_analytics.find_one({"short_id": short_url})

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
    async with db_cm as db:
        is_valid = await db.urls.find_one({"short_url": short_url})
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Url not found"
            )
        result = await db.urls.delete_one({"short_url": short_url})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            )
        return {"message": "Url data successfully erased"}
