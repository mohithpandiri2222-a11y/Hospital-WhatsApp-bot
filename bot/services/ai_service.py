"""
AI-powered fallback for unrecognized WhatsApp messages.

Uses the Groq inference API to answer general health questions,
suggest departments, and guide patients.  Never touches the database
or performs any booking action.
"""

import os
from groq import Groq

# ── Configuration ────────────────────────────────────────────

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set. "
        "Add it to your .env file or export it before starting the app."
    )

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

client = Groq(api_key=GROQ_API_KEY)

# ── Emergency / Red-Flag Keywords ────────────────────────────
# If ANY of these phrases appear in the user's message, the AI
# is bypassed entirely and an urgent-care message is returned.
# Add new phrases here as needed — matching is case-insensitive.

EMERGENCY_KEYWORDS: tuple[str, ...] = (
    "chest pain",
    "difficulty breathing",
    "can't breathe",
    "cant breathe",
    "severe bleeding",
    "unconscious",
    "unresponsive",
    "stroke",
    "severe allergic reaction",
)

EMERGENCY_RESPONSE = (
    "🚨 *EMERGENCY DETECTED*\n\n"
    "Your message suggests a medical emergency.\n\n"
    "🔴 Please *call emergency services immediately* or go to the "
    "nearest Emergency Room (ER).\n\n"
    "Do NOT wait for a WhatsApp reply in a life-threatening situation.\n\n"
    "Emergency Helpline: *112* (India) / *911* (US)"
)

# ── System Prompt ────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are ClinicFlow, a helpful hospital WhatsApp assistant. "
    "Help patients with general questions about symptoms, departments, "
    "and hospital information. "
    "You CANNOT book, modify, or cancel appointments — always direct "
    "patients to type 'hi' to start booking. "
    "You are not a doctor and must not give diagnoses, dosages, or "
    "treatment instructions — only suggest which department to visit. "
    "Keep responses under 100 words. "
    "Be friendly, professional, and reply in the same language the "
    "patient used.\n\n"
    "Available hospital departments:\n"
    "1. Cardiology — chest-related concerns, heart specialist\n"
    "2. General OPD — fever, cold, infections, stomach issues, general health problems\n"
    "3. Gynecology — women's health\n"
    "4. Orthopedics — bones, joints, injuries\n"
    "5. Pediatrics — children's health\n\n"
    "IMPORTANT: Only suggest departments from the list above. "
    "Never invent or mention departments that are not listed. "
    "If the patient needs a specialist that is not available "
    "(e.g. Ophthalmology, Dermatology, ENT), honestly tell them "
    "that department is not currently available at this hospital "
    "and suggest contacting hospital staff for a referral."
)

# ── Fallback Message ────────────────────────────────────────

FALLBACK_MESSAGE = (
    "I couldn't understand that. Please type 'hi' to book an "
    "appointment or contact hospital staff."
)

# ── Public API ──────────────────────────────────────────────


def get_ai_response(user_message: str, context: str | None = None) -> str:
    """Return an AI-generated response for a general patient query.

    Parameters
    ----------
    user_message : str
        The raw text the patient sent on WhatsApp.
    context : str | None
        Optional situational context (current state, selected department,
        etc.) folded into the prompt.  Must never be used to let the AI
        infer or perform a booking action.

    Returns
    -------
    str
        The response to send back to the patient.  Guaranteed to never
        raise — on any error the fixed *FALLBACK_MESSAGE* is returned.
    """

    # ── Red-flag short-circuit (no API call) ──
    msg_lower = user_message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in msg_lower:
            return EMERGENCY_RESPONSE

    # ── Build messages list ──
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({
            "role": "system",
            "content": (
                f"Current conversation context: {context}. "
                "Use this for situational awareness only — do NOT "
                "attempt any booking actions based on this context."
            ),
        })

    messages.append({"role": "user", "content": user_message})

    # ── Call Groq ──
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.0,
            max_tokens=150,
            timeout=8,
        )
        reply = chat_completion.choices[0].message.content
        return reply.strip() if reply else FALLBACK_MESSAGE

    except Exception:
        # Timeout, API error, malformed response — never propagate.
        return FALLBACK_MESSAGE
