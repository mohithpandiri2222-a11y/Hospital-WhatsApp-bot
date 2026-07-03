import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM  = os.getenv("TWILIO_WHATSAPP_FROM")
    ADMIN_PHONE  = os.getenv("ADMIN_PHONE")
    DB_PATH      = os.getenv("DATABASE_PATH", "hospital.db")
    FLASK_ENV    = os.getenv("FLASK_ENV", "production")
    ADMIN_PASSWORD   = os.getenv("ADMIN_PASSWORD", "hospital@123")
    ADMIN_SECRET_URL = os.getenv("ADMIN_SECRET_URL", "secret-abc123")
    SECRET_KEY       = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
