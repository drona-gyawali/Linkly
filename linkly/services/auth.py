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

    # for basic login
    async def create_user(self, name: str, email: EmailStr, password: str | None):
        hashed = pwd_context.hash(password) if password else None
        new_user = MongoUser(name=name, email=email, password=hashed, oauth=False)
        await self.db.users.insert_one(new_user.dict(by_alias=True))
        return new_user

    # for oauth login
    async def create_oauth_user(self, name: str, email: EmailStr):
        new_user = MongoUser(name=name, email=email, password=None, oauth=True)
        await self.db.users.insert_one(new_user.dict(by_alias=True))
        return new_user

    # main logic to check outh users identity
    async def get_or_create_oauth_user(self, name: str, email: EmailStr):
        user = await self.find_by_email(email)
        if user:
            return user
        return await self.create_oauth_user(name, email)

    def verify_password(self, plain_password: str, hashed_password: str | None) -> bool:
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)
