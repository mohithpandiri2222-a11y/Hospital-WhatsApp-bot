# 🏥 Hospital WhatsApp Appointment Bot

A WhatsApp chatbot that lets patients book, cancel, and view hospital appointments — built with Python + Flask + Twilio.

---

## 💬 What the Patient Sees

```
Patient:  hi
Bot:      🏥 Welcome to City Hospital!
          Select Department:
          1. Cardiology
          2. General OPD
          3. Gynecology
          4. Orthopedics
          5. Pediatrics

Patient:  2
Bot:      🏥 General OPD
          Choose your doctor:
          1. Dr. Ramesh Kumar
          2. Dr. Priya Sharma

Patient:  1
Bot:      👨‍⚕️ Dr. Ramesh Kumar
          Choose appointment date:
          1. Mon, 09 Jun
          2. Tue, 10 Jun
          ...

Patient:  1
Bot:      📅 Mon, 09 Jun
          Available time slots:
          1. 09:00
          2. 09:15
          3. 09:30
          ...

Patient:  2
Bot:      Slot selected: 09:15
          Please reply with your full name.

Patient:  Rahul Sharma
Bot:      ✅ Appointment Confirmed!
          👤 Rahul Sharma
          🏥 General OPD
          👨‍⚕️ Dr. Ramesh Kumar
          📅 Mon, 09 Jun
          ⏰ 09:15
          🎫 Token No: 3
```

---

## ⚙️ Setup (Step by Step)

### Step 1 — Clone & Setup

```bash
cd hospital-whatsapp-demo
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2 — Add your Twilio credentials

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and fill in your real Twilio values:
```
TWILIO_ACCOUNT_SID=ACxxxxxxx       ← from twilio.com console
TWILIO_AUTH_TOKEN=xxxxxxx          ← from twilio.com console
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886   ← Twilio sandbox number
ADMIN_PHONE=whatsapp:+91XXXXXXXXXX ← your own phone (for daily report)
```

> Get Twilio free trial: https://www.twilio.com/try-twilio
> Activate WhatsApp sandbox: Twilio Console → Messaging → Try it out → Send a WhatsApp message

### Step 3 — Run the server

```bash
python app.py
```

You should see:
```
✅ Doctors seeded
✅ Database ready: hospital.db
🏥 Hospital WhatsApp Bot starting...
 * Running on http://127.0.0.1:5000
```

### Step 4 — Expose your local server with ngrok

In a **new terminal** tab:
```bash
ngrok http 5000
```

Copy the HTTPS URL it gives you, e.g.:
```
https://abc123.ngrok-free.app
```

### Step 5 — Connect Twilio to your bot

1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Click **Sandbox Settings**
3. In "When a message comes in", paste:
   ```
   https://abc123.ngrok-free.app/whatsapp-webhook
   ```
4. Set method to **POST**
5. Save

### Step 6 — Test it!

From your phone, send **"hi"** to the Twilio sandbox WhatsApp number.
The bot should reply instantly.

---

## 📁 Project Structure

```
hospital-whatsapp-demo/
├── app.py                          # Entry point + scheduler
├── config.py                       # Env vars
├── requirements.txt
├── .env.example
│
├── db/
│   ├── connection.py               # SQLite connect + seed doctors
│   └── schema.sql                  # All table definitions
│
├── services/
│   ├── whatsapp_service.py         # Twilio: send messages
│   ├── session_service.py          # Track patient conversation state
│   ├── appointment_service.py      # Book / cancel / check slots
│   └── chatbot_service.py          # 🤖 Main conversation state machine
│
├── routes/
│   └── webhook_routes.py           # POST /whatsapp-webhook
│
└── jobs/
    └── appointment_reminder.py     # Daily 9AM reminder + admin report
```

---

## 🩺 Doctors Pre-loaded (Demo)

| Doctor | Department | Days | Slots |
|--------|-----------|------|-------|
| Dr. Ramesh Kumar | General OPD | Mon–Fri | 9AM–1PM, every 15 min |
| Dr. Priya Sharma | General OPD | Mon/Wed/Fri | 10AM–2PM, every 15 min |
| Dr. Anil Verma | Orthopedics | Tue/Thu/Sat | 9AM–12PM, every 20 min |
| Dr. Sunita Rao | Gynecology | Mon–Thu | 10AM–1PM, every 20 min |
| Dr. Kiran Mehta | Cardiology | Mon/Wed/Fri | 9AM–12PM, every 30 min |
| Dr. Deepak Singh | Pediatrics | Mon–Fri | 9AM–1PM, every 15 min |

---

## 🤖 Patient Commands (any time)

| Command | Action |
|---------|--------|
| hi / hello / book | Start booking flow |
| status | View upcoming appointment |
| cancel | Cancel upcoming appointment |
| menu | Go back to main menu |

---

## 🚀 Deploy to Render (free)

1. Push to GitHub
2. Go to render.com → New Web Service → Connect repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`
5. Add env vars from your `.env`
6. Deploy → copy the Render URL → update Twilio webhook

---

## 💰 Client Pitch (for small hospitals/clinics)

> "Your receptionist spends 2–3 hours/day taking appointment calls.
> This bot handles it 24/7 on WhatsApp automatically.
> Patients get instant confirmation + token number + reminder.
> ₹5,000–₹8,000/month setup + maintenance."
