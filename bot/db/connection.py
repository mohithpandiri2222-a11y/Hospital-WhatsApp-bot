import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with open("db/schema.sql") as f:
        sql = f.read()
    conn = get_db()
    conn.executescript(sql)
    conn.commit()

    # Seed doctors (only if table is empty)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM doctors")
    if cur.fetchone()[0] == 0:
        doctors = [
            ("Dr. Ramesh Kumar",  "General OPD",  "Mon,Tue,Wed,Thu,Fri", 15, "09:00", "13:00"),
            ("Dr. Priya Sharma",  "General OPD",  "Mon,Wed,Fri",         15, "10:00", "14:00"),
            ("Dr. Anil Verma",    "Orthopedics",  "Tue,Thu,Sat",         20, "09:00", "12:00"),
            ("Dr. Sunita Rao",    "Gynecology",   "Mon,Tue,Wed,Thu",     20, "10:00", "13:00"),
            ("Dr. Kiran Mehta",   "Cardiology",   "Mon,Wed,Fri",         30, "09:00", "12:00"),
            ("Dr. Deepak Singh",  "Pediatrics",   "Mon,Tue,Wed,Thu,Fri", 15, "09:00", "13:00"),
        ]
        cur.executemany(
            "INSERT INTO doctors (name, department, available_days, slot_duration_mins, start_time, end_time) VALUES (?,?,?,?,?,?)",
            doctors
        )
        conn.commit()
        print("[OK] Doctors seeded")

    conn.close()
    print("[OK] Database ready: hospital.db")

if __name__ == "__main__":
    init_db()
