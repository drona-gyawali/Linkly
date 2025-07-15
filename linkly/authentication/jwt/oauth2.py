from typing import Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from linkly.authentication.jwt.token import verify_token
from linkly.database import get_db_instance as get_db
from linkly.services.auth import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)
):
    repo = UserRepository(db)
    token_data = verify_token(token)
    user = await repo.find_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def optional_current_user(
    Authorization: Optional[str] = Header(default=None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not Authorization:
        return None

    scheme, _, token = Authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
