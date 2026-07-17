"""
Chatbot state machine for hospital WhatsApp appointment booking.

States:
  start              → show welcome + departments
  choose_dept        → patient picked dept, show doctors
  choose_doctor      → patient picked doctor, show dates
  choose_date        → patient picked date, show slots
  choose_slot        → patient picked slot, ask for name
  confirm_name       → patient gave name, book appointment
  idle               → booking done, handle cancel/status/restart
"""

from datetime import datetime
from db.connection import get_db
from services.session_service import get_session, set_session, clear_session
from services.appointment_service import (
    get_departments, get_doctors_by_dept, get_available_dates,
    get_available_slots, book_appointment, cancel_latest_appointment,
    get_upcoming_appointment
)
from services.ai_service import get_ai_response

# ── Helpers ───────────────────────────────────────────────────

def fmt_date(d: str) -> str:
    """Convert 2025-06-10 → Tue, 10 Jun"""
    return datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b")

def numbered_list(items: list) -> str:
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

# ── Main Handler ─────────────────────────────────────────────

def handle_message(phone: str, text: str) -> str:
    text = text.strip().lower()
    session = get_session(phone)
    step = session["step"]
    data = session["temp_data"]

    # Global shortcuts — work from any state
    if text in ("cancel", "cancel appointment"):
        result = cancel_latest_appointment(phone)
        clear_session(phone)
        if result["success"]:
            return (
                f"Your appointment with {result['doctor']} on "
                f"{fmt_date(result['date'])} at {result['time']} has been cancelled.\n\n"
                "Type hi to book a new appointment."
            )
        return f"{result['message']}\n\nType hi to book a new appointment."

    if text in ("status", "my appointment", "appointment"):
        appt = get_upcoming_appointment(phone)
        if appt:
            return (
                f"*Your Upcoming Appointment*\n\n"
                f"{appt['department']}\n"
                f"{appt['doctor_name']}\n"
                f"{fmt_date(appt['appointment_date'])}\n"
                f"{appt['slot_time']}\n"
                f"Token No: *{appt['token_number']}*\n\n"
                "Type cancel to cancel this appointment."
            )
        return "No upcoming appointment found.\n\nType hi to book one."

    if text in ("hi", "hello", "hey", "book", "start", "menu", "0", "home"):
        return _step_welcome(phone)

    # State machine
    if step == "start" or step == "idle":
        return get_ai_response(text)

    elif step == "choose_dept":
        return _step_choose_dept(phone, text, data)

    elif step == "choose_doctor":
        return _step_choose_doctor(phone, text, data)

    elif step == "choose_date":
        return _step_choose_date(phone, text, data)

    elif step == "choose_slot":
        return _step_choose_slot(phone, text, data)

    elif step == "confirm_name":
        return _step_confirm_name(phone, text, data)

    return _step_welcome(phone)

# ── Step Functions ────────────────────────────────────────────

def _step_welcome(phone: str) -> str:
    depts = get_departments()
    set_session(phone, "choose_dept", {"depts": depts})
    return (
                "*Welcome to City Hospital*\n"
                "Book your appointment in seconds!\n\n"
                "*Select Department:*\n"
                f"{numbered_list(depts)}\n\n"
                "_Reply with the number (e.g. 1)_"
            )

def _step_choose_dept(phone: str, text: str, data: dict) -> str:
    depts = data.get("depts", get_departments())
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(depts)
    except Exception:
        return (
            f"Please select an option number (1-{len(depts)}) to continue booking.\n"
            "If you want to ask a general question, type cancel first."
        )

    dept = depts[idx]
    doctors = get_doctors_by_dept(dept)
    if not doctors:
        return f"No doctors available in {dept} right now. Type hi to go back."

    doctor_names = [d["name"] for d in doctors]
    set_session(phone, "choose_doctor", {"dept": dept, "doctors": doctors})
    return (
        f"*{dept}*\n\n"
        "*Choose your doctor:*\n"
        f"{numbered_list(doctor_names)}\n\n"
        "_Reply with the number_"
    )

def _step_choose_doctor(phone: str, text: str, data: dict) -> str:
    doctors = data.get("doctors", [])
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(doctors)
    except:
        return (
            f"Please select an option number (1-{len(doctors)}) to continue booking.\n"
            "If you want to ask a general question, type cancel first."
        )

    doctor = doctors[idx]
    dates = get_available_dates(doctor["id"])
    if not dates:
        return "No dates available for this doctor. Type hi to go back."

    set_session(phone, "choose_date", {
        "dept": data["dept"],
        "doctor": doctor,
        "dates": dates
    })
    date_labels = [fmt_date(d) for d in dates]
    return (
        f"*{doctor['name']}*\n"
        f"{data['dept']}\n\n"
        "*Choose appointment date:*\n"
        f"{numbered_list(date_labels)}\n\n"
        "_Reply with the number_"
    )

def _step_choose_date(phone: str, text: str, data: dict) -> str:
    dates = data.get("dates", [])
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(dates)
    except:
        return (
            f"Please select an option number (1-{len(dates)}) to continue booking.\n"
            "If you want to ask a general question, type cancel first."
        )

    chosen_date = dates[idx]
    doctor = data["doctor"]
    slots = get_available_slots(doctor["id"], chosen_date)

    if not slots:
        return "No slots available on this date. Type hi to pick another date."

    set_session(phone, "choose_slot", {
        "dept": data["dept"],
        "doctor": doctor,
        "date": chosen_date,
        "slots": slots
    })
    return (
        f"*{fmt_date(chosen_date)}*\n\n"
        "*Available time slots:*\n"
        f"{numbered_list(slots)}\n\n"
        "_Reply with the number_"
    )

def _step_choose_slot(phone: str, text: str, data: dict) -> str:
    slots = data.get("slots", [])
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(slots)
    except:
        return (
            f"Please select an option number (1-{len(slots)}) to continue booking.\n"
            "If you want to ask a general question, type cancel first."
        )

    chosen_slot = slots[idx]
    data["slot"] = chosen_slot
    set_session(phone, "confirm_name", data)
    return (
        f"Slot selected: *{chosen_slot}*\n\n"
        "Please reply with your *full name* to confirm the booking."
    )

def _step_confirm_name(phone: str, text: str, data: dict) -> str:
    # Treat any non-number, non-keyword text as the name
    name = text.strip().title()
    if len(name) < 2:
        return "Please enter your full name."

    doctor = data["doctor"]
    chosen_date = data["date"]

    # ── Re-check: block if doctor is on leave for chosen date ──
    db = get_db()
    on_leave = db.execute(
        "SELECT id FROM doctor_leaves WHERE doctor_id=? AND leave_date=?",
        (doctor["id"], chosen_date)
    ).fetchone()
    db.close()

    if on_leave:
        clear_session(phone)
        return (
            f"❌ Sorry! *{doctor['name']}* is not available on "
            f"*{fmt_date(chosen_date)}*.\n\n"
            "Please type 'hi' to book another appointment date."
        )

    result = book_appointment(
        phone=phone,
        name=name,
        doctor_id=doctor["id"],
        date=chosen_date,
        slot_time=data["slot"]
    )

    clear_session(phone)

    if not result["success"]:
        return f"{result['message']}\n\nType hi to try again."

    return (
        f"*Appointment Confirmed!*\n\n"
        f"Patient: *{result['name']}*\n"
        f"{result['department']}\n"
        f"{result['doctor']}\n"
        f"{fmt_date(result['date'])}\n"
        f"{result['time']}\n"
        f"Token No: *{result['token']}*\n\n"
        "Please arrive 10 mins early. Bring this token number.\n\n"
        "Type status to view appointment.\n"
        "Type cancel to cancel."
    )

