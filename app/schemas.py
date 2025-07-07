from pydantic import BaseModel


class UrlRequest(BaseModel):
    original_url: str


class UrlResponse(BaseModel):
    short_url: str
    original_url: str
