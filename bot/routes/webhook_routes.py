from flask import Blueprint, request
from services.chatbot_service import handle_message
from services.whatsapp_service import send_whatsapp
from db.connection import get_db

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/whatsapp-webhook", methods=["POST"])
def whatsapp_webhook():
    """
    Twilio sends a POST here every time a patient messages on WhatsApp.
    """
    from_number = request.form.get("From", "")   # e.g. whatsapp:+919876543210
    body        = request.form.get("Body", "").strip()

    if not from_number or not body:
        return "OK", 200

    # Log incoming message
    phone = from_number.replace("whatsapp:", "")
    db = get_db()
    db.execute(
        "INSERT INTO logs (phone, event, details) VALUES (?, 'incoming', ?)",
        (phone, body)
    )
    db.commit()
    db.close()

    # Get reply from chatbot
    reply = handle_message(from_number, body)

    # Send reply back
    send_whatsapp(from_number, reply)

    return "OK", 200
