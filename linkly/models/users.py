from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UrlOut(BaseModel):
    original_url: str
    short_id: str
    created_at: Optional[int] = 0
    expiry: Optional[int] = None


class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    email: EmailStr
    oauth: bool
    urls: List[UrlOut] = []

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Login(BaseModel):
    name: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
