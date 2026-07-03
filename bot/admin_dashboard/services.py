from db.connection import get_db
from services.session_service import clear_session
from datetime import datetime, timedelta
import csv
import io

def get_dashboard_stats():
    db = get_db()
    today = datetime.now().date().strftime("%Y-%m-%d")
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")

    today_count = db.execute(
        "SELECT COUNT(*) as c FROM appointments WHERE appointment_date=? AND status='booked'", (today,)
    ).fetchone()["c"]

    tomorrow_count = db.execute(
        "SELECT COUNT(*) as c FROM appointments WHERE appointment_date=? AND status='booked'", (tomorrow,)
    ).fetchone()["c"]

    patient_count = db.execute("SELECT COUNT(*) as c FROM patients").fetchone()["c"]
    doctor_count = db.execute("SELECT COUNT(*) as c FROM doctors").fetchone()["c"]
    db.close()

    return {
        "today": today_count,
        "tomorrow": tomorrow_count,
        "patients": patient_count,
        "doctors": doctor_count
    }

def get_appointments_for_date(date_str):
    db = get_db()
    rows = db.execute(
        """SELECT a.id, a.token_number, a.patient_name, a.patient_phone,
                  d.name as doctor_name, d.department, a.slot_time, a.status
           FROM appointments a JOIN doctors d ON a.doctor_id=d.id
           WHERE a.appointment_date=?
           ORDER BY a.token_number""",
        (date_str,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_all_appointments(date=None, doctor_id=None, department=None, status=None):
    db = get_db()
    query = """SELECT a.id, a.token_number, a.patient_name, a.patient_phone,
                      d.name as doctor_name, d.department, d.id as doctor_id,
                      a.appointment_date, a.slot_time, a.status
               FROM appointments a JOIN doctors d ON a.doctor_id=d.id
               WHERE 1=1"""
    params = []
    if date:
        query += " AND a.appointment_date=?"
        params.append(date)
    if doctor_id:
        query += " AND a.doctor_id=?"
        params.append(doctor_id)
    if department:
        query += " AND d.department=?"
        params.append(department)
    if status:
        query += " AND a.status=?"
        params.append(status)
    query += " ORDER BY a.appointment_date DESC, a.token_number"
    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]

def cancel_appointment(appt_id):
    db = get_db()
    
    # Fetch appointment details for notification
    appt = db.execute('''
        SELECT a.patient_phone, a.appointment_date, a.slot_time, d.name as doctor_name 
        FROM appointments a 
        JOIN doctors d ON a.doctor_id = d.id 
        WHERE a.id=?
    ''', (appt_id,)).fetchone()
    
    db.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appt_id,))
    db.commit()
    db.close()
    
    if appt:
        # Reset patient's chatbot session so they can interact normally
        clear_session(appt["patient_phone"])
        try:
            from services.whatsapp_service import send_whatsapp
            from datetime import datetime
            date_str = datetime.strptime(appt["appointment_date"], "%Y-%m-%d").strftime("%a, %d %b")
            msg = (
                f"⚠️ *Appointment Cancelled*\n\n"
                f"We apologize, but your appointment with *{appt['doctor_name']}* on "
                f"*{date_str}* at *{appt['slot_time']}* has been cancelled by the hospital.\n\n"
                "Please type *hi* to book a new slot."
            )
            send_whatsapp(appt["patient_phone"], msg)
        except Exception as e:
            print(f"[Admin Cancel] Error sending notification: {e}")

def complete_appointment(appt_id):
    db = get_db()
    db.execute("UPDATE appointments SET status='completed' WHERE id=?", (appt_id,))
    db.commit()
    db.close()

def get_all_doctors():
    db = get_db()
    doctors = db.execute("SELECT * FROM doctors ORDER BY department, name").fetchall()
    result = []
    for d in doctors:
        doc = dict(d)
        leaves = db.execute(
            "SELECT id, leave_date, reason FROM doctor_leaves WHERE doctor_id=? ORDER BY leave_date",
            (d["id"],)
        ).fetchall()
        doc["leaves"] = [dict(l) for l in leaves]
        result.append(doc)
    db.close()
    return result

def mark_doctor_leave(doctor_id, leave_date, reason=""):
    db = get_db()
    success = False
    try:
        # 1. Insert the leave record
        db.execute(
            "INSERT OR IGNORE INTO doctor_leaves (doctor_id, leave_date, reason) VALUES (?,?,?)",
            (doctor_id, leave_date, reason)
        )
        
        # 2. Find any existing appointments on this date for this doctor
        appts = db.execute('''
            SELECT a.id, a.patient_phone, a.slot_time, d.name as doctor_name 
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.id 
            WHERE a.doctor_id=? AND a.appointment_date=? AND a.status='booked'
        ''', (doctor_id, leave_date)).fetchall()
        
        # 3. Auto-cancel them and notify patients
        from services.whatsapp_service import send_whatsapp
        from datetime import datetime
        date_str = datetime.strptime(leave_date, "%Y-%m-%d").strftime("%a, %d %b")
        
        for appt in appts:
            db.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appt["id"],))
            # Reset patient's chatbot session so they can interact normally
            clear_session(appt["patient_phone"])
            msg = (
                f"⚠️ *Emergency Appointment Cancellation*\n\n"
                f"We apologize, but your appointment with *{appt['doctor_name']}* on "
                f"*{date_str}* at *{appt['slot_time']}* has been cancelled because the doctor had to take an emergency leave.\n\n"
                "Please type *hi* to book a new slot for a different day."
            )
            try:
                send_whatsapp(appt["patient_phone"], msg)
            except Exception as e:
                print(f"[Leave Auto-Cancel] Notification error for {appt['patient_phone']}: {e}")
                
        db.commit()
        success = True
    except Exception as e:
        print(f"[mark_doctor_leave] Error: {e}")
        success = False
    finally:
        db.close()
    return success

def remove_doctor_leave(leave_id):
    db = get_db()
    db.execute("DELETE FROM doctor_leaves WHERE id=?", (leave_id,))
    db.commit()
    db.close()

def get_all_patients(search=None):
    db = get_db()
    if search:
        rows = db.execute(
            """SELECT p.id, p.name, p.phone, p.created_at,
                      COUNT(a.id) as total_appts,
                      MAX(a.appointment_date) as last_appt
               FROM patients p LEFT JOIN appointments a ON p.phone=a.patient_phone
               WHERE p.name LIKE ? OR p.phone LIKE ?
               GROUP BY p.id ORDER BY p.created_at DESC""",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT p.id, p.name, p.phone, p.created_at,
                      COUNT(a.id) as total_appts,
                      MAX(a.appointment_date) as last_appt
               FROM patients p LEFT JOIN appointments a ON p.phone=a.patient_phone
               GROUP BY p.id ORDER BY p.created_at DESC"""
        ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_analytics_data():
    db = get_db()
    today = datetime.now().date()
    thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    # Per day (last 30 days)
    daily = db.execute(
        """SELECT appointment_date, COUNT(*) as count
           FROM appointments
           WHERE appointment_date >= ? AND appointment_date <= ? AND status != 'cancelled'
           GROUP BY appointment_date ORDER BY appointment_date""",
        (thirty_days_ago, today_str)
    ).fetchall()

    # Per department
    by_dept = db.execute(
        """SELECT d.department, COUNT(*) as count
           FROM appointments a JOIN doctors d ON a.doctor_id=d.id
           WHERE a.status != 'cancelled'
           GROUP BY d.department ORDER BY count DESC"""
    ).fetchall()

    # Per doctor
    by_doctor = db.execute(
        """SELECT d.name, COUNT(*) as count
           FROM appointments a JOIN doctors d ON a.doctor_id=d.id
           WHERE a.status != 'cancelled'
           GROUP BY d.name ORDER BY count DESC"""
    ).fetchall()

    # This month total
    this_month = datetime.now().strftime("%Y-%m")
    month_total = db.execute(
        "SELECT COUNT(*) as c FROM appointments WHERE appointment_date LIKE ? AND status != 'cancelled'",
        (f"{this_month}%",)
    ).fetchone()["c"]

    # Busiest day
    busiest_day_row = db.execute(
        """SELECT appointment_date, COUNT(*) as count
           FROM appointments WHERE status != 'cancelled'
           GROUP BY appointment_date ORDER BY count DESC LIMIT 1"""
    ).fetchone()

    # Busiest doctor
    busiest_doctor_row = db.execute(
        """SELECT d.name, COUNT(*) as count
           FROM appointments a JOIN doctors d ON a.doctor_id=d.id
           WHERE a.status != 'cancelled'
           GROUP BY d.name ORDER BY count DESC LIMIT 1"""
    ).fetchone()

    db.close()
    return {
        "daily": [dict(r) for r in daily],
        "by_dept": [dict(r) for r in by_dept],
        "by_doctor": [dict(r) for r in by_doctor],
        "month_total": month_total,
        "busiest_day": dict(busiest_day_row) if busiest_day_row else None,
        "busiest_doctor": dict(busiest_doctor_row) if busiest_doctor_row else None
    }

def export_csv(appointments):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Token", "Patient Name", "Phone", "Doctor", "Department", "Date", "Time", "Status"])
    for a in appointments:
        writer.writerow([
            a["token_number"], a["patient_name"], a["patient_phone"],
            a["doctor_name"], a["department"], a["appointment_date"],
            a["slot_time"], a["status"]
        ])
    output.seek(0)
    return output.getvalue()
