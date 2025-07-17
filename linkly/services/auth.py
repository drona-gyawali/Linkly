from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from pydantic import EmailStr

from linkly.utils.dtype import MongoUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def find_by_name(self, name: str):
        return await self.db.users.find_one({"name": name})

    async def find_by_email(self, email: EmailStr):
        return await self.db.users.find_one({"email": email})

    async def find_by_id(self, user_id: str):
        return await self.db.users.find_one({"_id": ObjectId(user_id)})

    # for oauth login - fixed to return the inserted document with _id
    async def create_oauth_user(self, name: str, email: EmailStr):
        new_user = MongoUser(name=name, email=email, password=None, oauth=True)
        result = await self.db.users.insert_one(new_user.dict(by_alias=True))
        created_user = await self.find_by_id(str(result.inserted_id))
        return created_user

    # main logic to check oauth users identity
    async def get_or_create_oauth_user(self, name: str, email: EmailStr):
        user = await self.find_by_email(email)
        if user:
            return user
        return await self.create_oauth_user(name, email)

    def verify_password(self, plain_password: str, hashed_password: str | None) -> bool:
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    async def get_user_urls(self, user_id: ObjectId):
        cursor = self.db.urls.find({"user_id": ObjectId(user_id)})
        return [
            {
                "original_url": url["original_url"],
                "short_id": url["short_id"],
                "created_at": url["created_at"],
                "expiry": url["expiry"],
            }
            async for url in cursor
        ]
