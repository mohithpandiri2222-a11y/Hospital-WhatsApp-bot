from datetime import datetime, timedelta
from db.connection import get_db

DAYS_MAP = {
    "Mon": 0, "Tue": 1, "Wed": 2,
    "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6
}
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ── Departments ──────────────────────────────────────────────

def get_departments() -> list:
    db = get_db()
    rows = db.execute("SELECT DISTINCT department FROM doctors ORDER BY department").fetchall()
    db.close()
    return [r["department"] for r in rows]

# ── Doctors ──────────────────────────────────────────────────

def get_doctors_by_dept(department: str) -> list:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM doctors WHERE department=?", (department,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_doctor(doctor_id: int) -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    db.close()
    return dict(row) if row else None

# ── Available Dates ──────────────────────────────────────────

def get_available_dates(doctor_id: int, days_ahead: int = 7) -> list:
    """Return next N available dates for a doctor."""
    doctor = get_doctor(doctor_id)
    if not doctor:
        return []

    available_day_nums = [
        DAYS_MAP[d.strip()]
        for d in doctor["available_days"].split(",")
        if d.strip() in DAYS_MAP
    ]

    dates = []
    today = datetime.now().date()
    for i in range(1, days_ahead + 1):
        d = today + timedelta(days=i)
        if d.weekday() in available_day_nums:
            dates.append(d.strftime("%Y-%m-%d"))
        if len(dates) == 5:  # max 5 dates to show
            break
    return dates

# ── Available Slots ──────────────────────────────────────────

def get_available_slots(doctor_id: int, date: str) -> list:
    """Return list of free time slots for a doctor on a date."""
    doctor = get_doctor(doctor_id)
    if not doctor:
        return []

    # Generate all slots
    start_h, start_m = map(int, doctor["start_time"].split(":"))
    end_h,   end_m   = map(int, doctor["end_time"].split(":"))
    duration = doctor["slot_duration_mins"]

    all_slots = []
    current = datetime(2000, 1, 1, start_h, start_m)
    end     = datetime(2000, 1, 1, end_h,   end_m)
    while current < end:
        all_slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration)

    # Remove already booked slots
    db = get_db()
    booked = db.execute(
        "SELECT slot_time FROM appointments WHERE doctor_id=? AND appointment_date=? AND status='booked'",
        (doctor_id, date)
    ).fetchall()
    db.close()
    booked_times = {r["slot_time"] for r in booked}

    return [s for s in all_slots if s not in booked_times]

# ── Book Appointment ─────────────────────────────────────────

def book_appointment(phone: str, name: str, doctor_id: int, date: str, slot_time: str) -> dict:
    """Book a slot and return appointment details."""
    db = get_db()

    # Double-check slot is still free
    conflict = db.execute(
        "SELECT id FROM appointments WHERE doctor_id=? AND appointment_date=? AND slot_time=? AND status='booked'",
        (doctor_id, date, slot_time)
    ).fetchone()
    if conflict:
        db.close()
        return {"success": False, "message": "Sorry, this slot was just taken. Please choose another."}

    # Generate token number (count of appointments for this doctor on this date + 1)
    count = db.execute(
        "SELECT COUNT(*) as c FROM appointments WHERE doctor_id=? AND appointment_date=?",
        (doctor_id, date)
    ).fetchone()["c"]
    token = count + 1

    # Insert
    db.execute(
        """INSERT INTO appointments
           (patient_phone, patient_name, doctor_id, appointment_date, slot_time, token_number, status)
           VALUES (?, ?, ?, ?, ?, ?, 'booked')""",
        (phone, name, doctor_id, date, slot_time, token)
    )

    # Save patient
    db.execute(
        "INSERT INTO patients (phone, name) VALUES (?, ?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name",
        (phone, name)
    )
    db.commit()
    db.close()

    doctor = get_doctor(doctor_id)
    return {
        "success": True,
        "token": token,
        "doctor": doctor["name"],
        "department": doctor["department"],
        "date": date,
        "time": slot_time,
        "name": name
    }

# ── Cancel Appointment ───────────────────────────────────────

def cancel_latest_appointment(phone: str) -> dict:
    """Cancel the most recent booked appointment for a patient."""
    db = get_db()
    appt = db.execute(
        """SELECT a.*, d.name as doctor_name FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           WHERE a.patient_phone=? AND a.status='booked'
           ORDER BY a.appointment_date, a.slot_time LIMIT 1""",
        (phone,)
    ).fetchone()

    if not appt:
        db.close()
        return {"success": False, "message": "No upcoming appointment found."}

    db.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appt["id"],))
    db.commit()
    db.close()
    return {
        "success": True,
        "doctor": appt["doctor_name"],
        "date": appt["appointment_date"],
        "time": appt["slot_time"]
    }

# ── View Appointment ─────────────────────────────────────────

def get_upcoming_appointment(phone: str) -> dict:
    """Get next booked appointment for a patient."""
    db = get_db()
    appt = db.execute(
        """SELECT a.*, d.name as doctor_name, d.department FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           WHERE a.patient_phone=? AND a.status='booked'
           ORDER BY a.appointment_date, a.slot_time LIMIT 1""",
        (phone,)
    ).fetchone()
    db.close()
    return dict(appt) if appt else None
