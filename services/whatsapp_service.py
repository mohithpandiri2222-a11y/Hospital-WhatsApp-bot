from twilio.rest import Client
from config import Config

client = Client(Config.TWILIO_SID, Config.TWILIO_TOKEN)

def send_whatsapp(to_phone: str, message: str):
    """
    Send a WhatsApp message via Twilio.
    to_phone should be in format: whatsapp:+91XXXXXXXXXX
    """
    try:
        try:
            print("BOT RESPONSE:", message.encode("ascii", "ignore").decode("ascii"), flush=True)
        except Exception:
            pass
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        msg = client.messages.create(
            from_=Config.TWILIO_FROM,
            to=to_phone,
            body=message
        )
        return msg.sid
    except Exception as e:
        print(f"[WhatsApp Error] {e}")
        return None