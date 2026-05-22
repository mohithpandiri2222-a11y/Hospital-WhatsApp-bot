from flask import Flask, jsonify
from config import Config
from routes.webhook_routes import webhook_bp
from db.connection import init_db
from apscheduler.schedulers.background import BackgroundScheduler
from jobs.appointment_reminder import send_appointment_reminders
import atexit

app = Flask(__name__)

# ── Register Blueprints ───────────────────────────────────────
app.register_blueprint(webhook_bp)

# ── Health Check ──────────────────────────────────────────────
@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "Hospital WhatsApp Bot"})

# ── Scheduler (reminders at 9 AM daily) ──────────────────────
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=send_appointment_reminders,
    trigger="cron",
    hour=9,
    minute=0,
    id="daily_reminders"
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ── Start ─────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("[START] Hospital WhatsApp Bot starting...")
    print("[INFO] Webhook: POST /whatsapp-webhook")
    app.run(debug=True, port=5000, use_reloader=False)
