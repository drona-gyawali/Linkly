import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
LOCAL_HOST = os.getenv("LOCAL_HOST")
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# you can use api url from https://ip-api.com/json service : this for analytics purpose
# keeping secret because of some concern
IP_DETAILS_URL = os.getenv("IP_DETAILS_URL")
