"""
This module contains APIs used in our product
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db, get_db_instance
from app.schemas import UrlRequest, UrlResponse
from app.services.shortner import (
    delete_url,
    get_url_analytics,
    resolves_url,
    shorten_url,
    url_analytics,
)
from app.settings import LOCAL_HOST

router = APIRouter(tags=["Url"])


@router.post("/shorten", response_model=UrlResponse)
async def create_short_url(
    data: UrlRequest, db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Take the data object and return json response.
    """
    short = await shorten_url(data.original_url, db)
    return UrlResponse(original_url=data.original_url, short_url=short)


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
    short_url = short_url = LOCAL_HOST + f"/{short_id}"
    _del = await delete_url(short_url=short_url, db_cm=db_cm)
    return _del
