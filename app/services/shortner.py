"""
This module contains the service level logic for the api.
"""
from app.database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.encode_url import ShortIdGenerator
from fastapi import Depends, Request
from app.settings import LOCAL_HOST, IP_DETAILS_URL
from fastapi import HTTPException, status
from datetime import datetime, timezone
import httpx

async def shorten_url(
    original_url:str,
    db_cm: AsyncIOMotorDatabase = Depends(get_db)
) -> str:
    """
    Take the long url as input and return working short url
    """
    try:
        async with db_cm as db:
            hash = ShortIdGenerator.generate()
            short_url = LOCAL_HOST + f'/{hash}'
            await db.urls.insert_one({
                "original_url": original_url,
                "short_url": short_url
            })
            return short_url
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

async def resolves_url(
    short_url: str,
    db_cm = Depends(get_db)
):
    """
    Accept the short url and return the original url
    """
    try:
        async with db_cm as db:
            url_doc = await db.urls.find_one({"short_url": short_url})
            if not url_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail={"error": f'{short_url} doenot exist in system'}
                    )
            return url_doc["original_url"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

async def url_analytics(
    short_url: str, 
    request: Request,
    db_cm
):
    """
    Manage the analytical data for the url.
    """
    header = request.headers.get("user-agent", "unknown")
    user_ip = request.client.host
    # yo chai yesso test ko lagi ho hai..
    if user_ip == "127.0.0.1":
        user_ip = "8.8.8.8"

    location = None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(IP_DETAILS_URL +f'/{user_ip}')
            if r.status_code == 200:
                data = r.json()
                city = data.get("city", "")
                country= data.get("country", "")
                location = ", ".join(filter(None, [city, country])) or None
    except Exception:
        location = None

    click_info = {
        "user_agent": header,
        "ip": user_ip,
        "timestamp": datetime.now(timezone.utc),
        "location": location
    }

    async with db_cm as db:
        await db.url_analytics.update_one(
            {"short_id": short_url},
            {
                "$inc": {"clicks": 1},
                "$push": {"click_details": click_info}
                },
            upsert=True,
        )


async def get_url_analytics(
    short_url: str, 
    db_cm
):
    async with db_cm as db:
        analytics_doc = await db.url_analytics.find_one({"short_id": short_url})

        if not analytics_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analytics data not found for this short URL"
            )

        # Converting _id and timestamps for JSON serialization
        analytics_doc["_id"] = str(analytics_doc["_id"])
        for entry in analytics_doc.get("click_details", []):
            entry["timestamp"] = entry["timestamp"].isoformat()

        return analytics_doc


async def delete_url(
        short_url:str,
        db_cm
):
    async with db_cm as db:
        is_valid = await db.urls.find_one({"short_url":short_url})
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Url not found")
        result = await db.urls.delete_one({"short_url":short_url})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong"
            )
        return {"message": 'Url data successfully erased'}
        
