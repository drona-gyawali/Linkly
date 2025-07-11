from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from linkly.authentication.jwt.token import create_access_token
from linkly.authentication.oauth import oauth
from linkly.database import get_db_instance as get_db
from linkly.models.users import Login, Token, UserRegister
from linkly.services.auth import UserRepository

router = APIRouter(tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register")
async def register(data: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    repo = UserRepository(db)
    name_check = await repo.find_by_name(data.name)
    email_check = await repo.find_by_email(data.email)
    if name_check or email_check:
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


# GitHub OAuth
@router.get("/auth/github")
async def auth_github(request: Request):
    redirect_uri = request.url_for("auth_github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


# GitHub OAuth Callback
@router.get("/auth/github/callback")
async def auth_github_callback(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
):
    token = await oauth.github.authorize_access_token(request)

    # Getting GitHub profile
    github_user_resp = await oauth.github.get("user", token=token)
    profile = github_user_resp.json()
    email = profile.get("email")

    if not email:
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = emails_resp.json()
        email = next(
            (e["email"] for e in emails if e["primary"] and e["verified"]), None
        )

    if not email:
        raise HTTPException(
            status_code=400, detail="GitHub account has no accessible email"
        )

    name = profile.get("name") or profile.get("login")

    repo = UserRepository(db)
    user = await repo.get_or_create_oauth_user(name=name, email=email)

    access_token = create_access_token(str(user["_id"]))
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})


# Google Auth
@router.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Get token from Google
    token = await oauth.google.authorize_access_token(request)

    # Parse user info from id token
    user_info = await oauth.google.parse_id_token(request, token)
    email = user_info.get("email")
    name = user_info.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    repo = UserRepository(db)
    user = await repo.get_or_create_oauth_user(name=name, email=email)

    access_token = create_access_token(str(user["_id"]))
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})
