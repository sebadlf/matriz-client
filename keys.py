import os

from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

IOL_USERNAME = os.getenv("IOL_USERNAME")
IOL_PASSWORD = os.getenv("IOL_PASSWORD")

OMS_URL = os.getenv("OMS_URL") or ""
OMS_USER = os.getenv("OMS_USER") or ""
OMS_PASSWORD = os.getenv("OMS_PASSWORD") or ""
OMS_API_KEY_ID = os.getenv("OMS_API_KEY_ID") or ""
OMS_API_KEY_SECRET = os.getenv("OMS_API_KEY_SECRET") or ""

LEGA_LENTITY = os.getenv("LEGA_LENTITY") or ""
