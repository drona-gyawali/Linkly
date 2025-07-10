from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from linkly.authentication.jwt.token import verify_token
from linkly.services.auth import UserRepository
from linkly.database import get_db_instance as get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    repo = UserRepository(db)
    token_data = verify_token(token)
    user = await repo.find_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
