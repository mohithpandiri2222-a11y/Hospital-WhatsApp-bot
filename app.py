from flask import Flask, jsonify
from config import Config
from routes.webhook_routes import webhook_bp
from db.connection import init_db
from apscheduler.schedulers.background import BackgroundScheduler
from jobs.appointment_reminder import send_appointment_reminders
import atexit
import requests
import os

app = Flask(__name__)

# ── Initialize DB (runs on both gunicorn and direct python) ──
init_db()

# ── Register Blueprints ───────────────────────────────────────
app.register_blueprint(webhook_bp)

# ── Health Check ──────────────────────────────────────────────
@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "Hospital WhatsApp Bot"})

# ── Self-ping to prevent Render free tier sleep ───────────────
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL", "")
    if url:
        try:
            requests.get(url, timeout=10)
            print("[PING] Keep-alive ping sent")
        except Exception as e:
            print(f"[PING] Failed: {e}")

# ── Scheduler ─────────────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=send_appointment_reminders,
    trigger="cron",
    hour=9,
    minute=0,
    id="daily_reminders"
)
# Ping every 14 minutes to keep Render free tier awake
scheduler.add_job(
    func=keep_alive,
    trigger="interval",
    minutes=14,
    id="keep_alive"
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ── Start ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[START] Hospital WhatsApp Bot starting...")
    print("[INFO] Webhook: POST /whatsapp-webhook")
    app.run(debug=Config.FLASK_ENV == "development", port=5000, use_reloader=False)
