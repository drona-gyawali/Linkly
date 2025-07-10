from motor.motor_asyncio import AsyncIOMotorDatabase
from linkly.utils.dtype import MongoUser
from bson import ObjectId
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def find_by_name(self, name: str):
        return await self.db.users.find_one({"name": name})

    async def find_by_id(self, user_id: str):
        return await self.db.users.find_one({"_id": ObjectId(user_id)})

    async def create_user(self, name: str, email: str, password: str):
        hashed = pwd_context.hash(password)
        new_user = MongoUser(name=name, email=email, password=hashed)
        await self.db.users.insert_one(new_user.dict(by_alias=True))
        return new_user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
