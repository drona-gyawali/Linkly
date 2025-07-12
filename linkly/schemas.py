from typing import Optional

from pydantic import BaseModel


class UrlRequest(BaseModel):
    original_url: str
    expiry: Optional[int]


class UrlResponse(BaseModel):
    short_url: str
    original_url: str
    expiry: Optional[int]
