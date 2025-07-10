"""
Pydantic model configuration to support custom data types.

- `arbitrary_types_allowed = True` enables Pydantic models to accept
  and work with non-standard or user-defined types (e.g., ObjectId).
- This is necessary when integrating MongoDB ObjectId or other complex
  types that Pydantic doesn't natively understand.

kindly visit for more information: https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi/#database-models
"""

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            return ValueError(f"Invalid Object: {str(v)}")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        from pydantic import core_schema

        return core_schema.str_schema()


class MongoUser(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: EmailStr
    password: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
