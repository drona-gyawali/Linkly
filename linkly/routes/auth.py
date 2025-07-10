from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from linkly.authentication.jwt.token import create_access_token
from linkly.database import get_db_instance as get_db
from linkly.models.users import Login, Token, UserRegister
from linkly.services.auth import UserRepository

router = APIRouter(tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register")
async def register(data: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    repo = UserRepository(db)
    existing = await repo.find_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    await repo.create_user(data.name, data.email, data.password)
    return {"msg": "User registered"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.find_by_name(form_data.username)
    if not user or not repo.verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(str(user["_id"]))
    return {"access_token": access_token, "token_type": "bearer"}
