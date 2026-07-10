"""
Runs every day at 9:00 AM.
Sends WhatsApp reminder to every patient with an appointment tomorrow.
Also sends daily summary to admin.
"""

from db.connection import get_db
from services.whatsapp_service import send_whatsapp
from config import Config
from datetime import datetime, timedelta

def send_appointment_reminders():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    db = get_db()

    appointments = db.execute(
        """SELECT a.*, d.name as doctor_name, d.department
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           WHERE a.appointment_date = ? AND a.status = 'booked'""",
        (tomorrow,)
    ).fetchall()

    count = 0
    for appt in appointments:
        msg = (
            f"*Appointment Reminder*\n\n"
            f"Hi {appt['patient_name'] or 'Patient'},\n"
            f"Your appointment is *tomorrow*!\n\n"
            f"{appt['doctor_name']}\n"
            f"{appt['department']}\n"
            f"{appt['slot_time']}\n"
            f"Token No: *{appt['token_number']}*\n\n"
            "Please arrive 10 mins early. Type cancel to cancel."
        )
        send_whatsapp(f"whatsapp:{appt['patient_phone']}", msg)
        count += 1

    # Send summary to admin
    if Config.ADMIN_PHONE:
        summary = (
            f"*Tomorrow's Appointments — {tomorrow}*\n\n"
            f"Total booked: *{count}*\n\n"
        )
        for appt in appointments:
            summary += f"• {appt['patient_name']} — {appt['doctor_name']} @ {appt['slot_time']}\n"
        send_whatsapp(Config.ADMIN_PHONE, summary)

    db.close()
    print(f"[Reminder] Sent {count} reminders for {tomorrow}")
