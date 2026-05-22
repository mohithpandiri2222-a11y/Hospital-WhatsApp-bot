import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM  = os.getenv("TWILIO_WHATSAPP_FROM")
    ADMIN_PHONE  = os.getenv("ADMIN_PHONE")
    DB_PATH      = os.getenv("DATABASE_PATH", "hospital.db")
