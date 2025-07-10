"""
This module contains the collections for urls
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from linkly.utils.dtype import PyObjectId


class UrlDbObject(BaseModel):
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)
    original_url: str
    short_id: str
    user_id:  Optional[PyObjectId] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class ClickInfo(BaseModel):
    user_agent: str
    timestamp: datetime
    ip: Optional[str] = None
    location: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class UrlAnalytics(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    short_id: str
    clicks: int = 0
    click_details: List[ClickInfo] = []
    finger_print: List[str] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
