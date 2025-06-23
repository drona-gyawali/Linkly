"""
This module contains the collections for urls 
"""
from pydantic  import BaseModel, Field
from app.utils.dtype import PyObjectId
from bson import ObjectId
from typing import List
from datetime import datetime


class UrlDbObject(BaseModel):
    id:PyObjectId = Field(alias= '_id', default_factory=PyObjectId)
    original_url:str
    short_id:str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True

class ClickInfo(BaseModel):
    user_agent: str
    timestamp: datetime
    ip: str | None = None
    location: str | None = None

class UrlAnalytics(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    short_id: str
    clicks: int = 0
    click_details: List[ClickInfo] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}