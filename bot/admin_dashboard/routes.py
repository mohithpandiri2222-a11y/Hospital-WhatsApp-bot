from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, Response, make_response
)
from functools import wraps
from datetime import datetime, timedelta
from config import Config
from admin_dashboard import services as svc
from db.connection import get_db
import os

admin_bp = Blueprint(
    "admin", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/admin/static"
)

# ── Auth helpers ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated

# ── Login ─────────────────────────────────────────────────────

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if pwd == Config.ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        error = "Invalid password. Please try again."
    return render_template("admin/login.html", error=error)

@admin_bp.route("/secret-<token>")
def secret_login(token):
    if token == Config.ADMIN_SECRET_URL:
        session["admin_logged_in"] = True
        session.permanent = True
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))

@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))

# ── Dashboard ─────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
def dashboard():
    stats = svc.get_dashboard_stats()
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
    today_appts = svc.get_appointments_for_date(today_str)
    tomorrow_appts = svc.get_appointments_for_date(tomorrow_str)
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        today_appts=today_appts,
        tomorrow_appts=tomorrow_appts,
        today=today_str,
        tomorrow=tomorrow_str
    )

# ── Appointments ──────────────────────────────────────────────

@admin_bp.route("/appointments")
@login_required
def appointments():
    date = request.args.get("date", "")
    doctor_id = request.args.get("doctor_id", "")
    department = request.args.get("department", "")
    status = request.args.get("status", "")
    appts = svc.get_all_appointments(
        date=date or None,
        doctor_id=int(doctor_id) if doctor_id else None,
        department=department or None,
        status=status or None
    )
    db = get_db()
    doctors = db.execute("SELECT id, name, department FROM doctors ORDER BY name").fetchall()
    departments = db.execute("SELECT DISTINCT department FROM doctors ORDER BY department").fetchall()
    db.close()
    return render_template(
        "admin/appointments.html",
        appts=appts,
        doctors=[dict(d) for d in doctors],
        departments=[r["department"] for r in departments],
        filters={"date": date, "doctor_id": doctor_id, "department": department, "status": status}
    )

@admin_bp.route("/cancel-appointment/<int:appt_id>", methods=["POST"])
@login_required
def cancel_appointment(appt_id):
    svc.cancel_appointment(appt_id)
    flash("Appointment cancelled.", "success")
    return redirect(request.referrer or url_for("admin.appointments"))

@admin_bp.route("/complete-appointment/<int:appt_id>", methods=["POST"])
@login_required
def complete_appointment(appt_id):
    svc.complete_appointment(appt_id)
    flash("Appointment marked as completed.", "success")
    return redirect(request.referrer or url_for("admin.appointments"))

@admin_bp.route("/export-csv")
@login_required
def export_csv():
    date = request.args.get("date", "")
    doctor_id = request.args.get("doctor_id", "")
    department = request.args.get("department", "")
    status = request.args.get("status", "")
    appts = svc.get_all_appointments(
        date=date or None,
        doctor_id=int(doctor_id) if doctor_id else None,
        department=department or None,
        status=status or None
    )
    csv_data = svc.export_csv(appts)
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=appointments.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

# ── Doctors ───────────────────────────────────────────────────

@admin_bp.route("/doctors")
@login_required
def doctors():
    all_doctors = svc.get_all_doctors()
    today = datetime.now().date().strftime("%Y-%m-%d")
    return render_template("admin/doctors.html", doctors=all_doctors, today=today)

@admin_bp.route("/mark-leave", methods=["POST"])
@login_required
def mark_leave():
    doctor_id = request.form.get("doctor_id")
    leave_date = request.form.get("leave_date")
    reason = request.form.get("reason", "")
    if doctor_id and leave_date:
        svc.mark_doctor_leave(int(doctor_id), leave_date, reason)
        flash("Leave marked successfully.", "success")
    return redirect(url_for("admin.doctors"))

@admin_bp.route("/remove-leave/<int:leave_id>", methods=["POST"])
@login_required
def remove_leave(leave_id):
    svc.remove_doctor_leave(leave_id)
    flash("Leave removed.", "success")
    return redirect(url_for("admin.doctors"))

# ── Analytics ─────────────────────────────────────────────────

@admin_bp.route("/analytics")
@login_required
def analytics():
    data = svc.get_analytics_data()
    return render_template("admin/analytics.html", data=data)

# ── Patients ──────────────────────────────────────────────────

@admin_bp.route("/patients")
@login_required
def patients():
    search = request.args.get("search", "")
    all_patients = svc.get_all_patients(search=search or None)
    return render_template("admin/patients.html", patients=all_patients, search=search)
