-- PATIENTS
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT UNIQUE NOT NULL,
    age TEXT,
    last_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DOCTORS
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    available_days TEXT NOT NULL,   -- e.g. "Mon,Tue,Wed,Thu,Fri"
    slot_duration_mins INTEGER DEFAULT 15,
    start_time TEXT DEFAULT "09:00",
    end_time TEXT DEFAULT "13:00"
);

-- APPOINTMENTS
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_phone TEXT NOT NULL,
    patient_name TEXT,
    doctor_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,   -- YYYY-MM-DD
    slot_time TEXT NOT NULL,          -- HH:MM
    token_number INTEGER,
    status TEXT DEFAULT 'booked'
        CHECK (status IN ('booked','cancelled','completed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- SESSIONS (tracks where patient is in conversation)
CREATE TABLE IF NOT EXISTS sessions (
    phone TEXT PRIMARY KEY,
    step TEXT DEFAULT 'start',
    temp_data TEXT DEFAULT '{}',      -- JSON string for partial booking
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- LOGS
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT,
    event TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DOCTOR LEAVES
CREATE TABLE IF NOT EXISTS doctor_leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    leave_date TEXT NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    UNIQUE(doctor_id, leave_date)
);
