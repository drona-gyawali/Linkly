"""
This module contains APIs used in our product
"""

import httpx
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, Response, status)
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from motor.motor_asyncio import AsyncIOMotorDatabase

from linkly.database import get_db, get_db_instance
from linkly.schemas import UrlRequest, UrlResponse
from linkly.services.shortner import (
    delete_url,
    get_url_analytics,
    resolves_url,
    shorten_url,
    url_analytics
)
from linkly.authentication.jwt.oauth2 import get_current_user
from linkly.settings import LOCAL_HOST, QR_CODE_API

router = APIRouter(tags=["Url"])


@router.post("/shorten", response_model=UrlResponse)
async def create_short_url(
    data: UrlRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    short_url = await shorten_url(data.original_url, db, user["_id"])
    return UrlResponse(original_url=data.original_url, short_url=short_url)


@router.get("/{short_id}")
async def redirect_to_original(
    short_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db_instance),
):
    """
    Take the short url and redirect to the original url destination.
    Also track analytics in background
    """
    try:
        short_url = LOCAL_HOST + f"/{short_id}"
        original_url = await resolves_url(short_url, db)
        background_tasks.add_task(url_analytics, short_url, request, get_db_instance())
        return RedirectResponse(url=original_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong {str(e)}",
        )


@router.get("/analytics/{short_id}")
@cache(expire=180)
async def view_url_analytics(
    short_id: str,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    user: dict = Depends(get_current_user),
    db_cm: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Endpoint that gives the json data related to the Url, optionally filtered by UTM parameters.
    """
    short_url = LOCAL_HOST + f"/{short_id}"
    response = await get_url_analytics(
        short_url=short_url,
        db_cm=db_cm,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
    )
    return response


@router.get("/delete/{short_id}")
async def delete_content(short_id: str, db_cm: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Endpoint that delete the whole data of given short_id
    """
    short_url = LOCAL_HOST + f"/{short_id}"
    _del = await delete_url(short_url=short_url, db_cm=db_cm)
    return _del


@router.get("/create-qr-code/{short_id}")
async def generate_qr(short_id: str):
    """
    Endpoint that generates the qr code of the url
    """
    short_url = short_url = LOCAL_HOST + f"/{short_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(QR_CODE_API + short_url)
            if response.status_code == 200:
                return Response(content=response.content, media_type="image/png")
            else:
                raise Exception(f"Failed to get qr: status-{response.status_code}")
    except Exception as e:
        raise Exception(f"QR generation failed: {e}")
