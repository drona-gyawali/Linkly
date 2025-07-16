import os

from dotenv import load_dotenv

load_dotenv()


class Settings:

    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME")
    LOCAL_HOST = os.getenv("LOCAL_HOST")
    BASE62 = os.getenv("BASE62")

    IP_DETAILS_URL = os.getenv("IP_DETAILS_URL")
    QR_CODE_API = os.getenv("QR_CODE_API")

    secret = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM")
    acess_token_expiry = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    SESSION_SECRET = os.getenv("SESSION_SECRET")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

    redis_url = os.getenv("REDIS_URL", "redis://localhost")
    
settings = Settings()
