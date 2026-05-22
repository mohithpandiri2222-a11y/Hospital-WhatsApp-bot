import json
from db.connection import get_db

def get_session(phone: str) -> dict:
    """Get current session for a patient phone number."""
    db = get_db()
    row = db.execute("SELECT * FROM sessions WHERE phone=?", (phone,)).fetchone()
    db.close()
    if row:
        return {"step": row["step"], "temp_data": json.loads(row["temp_data"])}
    return {"step": "start", "temp_data": {}}

def set_session(phone: str, step: str, temp_data: dict = {}):
    """Create or update session for a patient."""
    db = get_db()
    db.execute(
        """INSERT INTO sessions (phone, step, temp_data, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(phone) DO UPDATE SET
             step=excluded.step,
             temp_data=excluded.temp_data,
             updated_at=CURRENT_TIMESTAMP""",
        (phone, step, json.dumps(temp_data))
    )
    db.commit()
    db.close()

def clear_session(phone: str):
    """Reset session back to start."""
    set_session(phone, "start", {})
