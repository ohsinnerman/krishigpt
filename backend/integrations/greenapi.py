"""
WhatsApp integration via Green-API (https://green-api.com/).

Unlike Twilio (which expects a synchronous TwiML reply), Green-API:
  1. POSTs an incoming-message notification (JSON) to our webhook.
  2. We reply by making a SEPARATE outgoing call to its sendMessage endpoint.

Webhook route: POST /webhook/greenapi  (wired in main.py)

Required env:
  GREENAPI_ID_INSTANCE   - your instance id (e.g. 1101xxxxxx)
  GREENAPI_API_TOKEN     - your instance api token
"""
import os, hashlib
import httpx

ID_INSTANCE = os.getenv("GREENAPI_ID_INSTANCE", "").strip()
API_TOKEN = os.getenv("GREENAPI_API_TOKEN", "").strip()
BASE = "https://api.green-api.com"

ONBOARDING_MSG = (
    "Welcome to KrishiGPT 🌾 I answer farming questions in 7 languages.\n"
    "Reply with your language:\n1=English\n2=हिन्दी\n3=ಕನ್ನಡ\n4=தமிழ்\n5=తెలుగు\n6=मराठी\n7=ਪੰਜਾਬੀ"
)
LANG_MAP = {"1": "en", "2": "hi", "3": "kn", "4": "ta", "5": "te", "6": "mr", "7": "pa"}

PINCODE_PROMPT = {
    "en": "Please send your 6-digit PIN code so I can give region-specific advice.",
    "hi": "कृपया अपना 6 अंकों का पिन कोड भेजें ताकि मैं आपके क्षेत्र के अनुसार सलाह दे सकूं।",
    "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ 6 ಅಂಕಿಯ ಪಿನ್ ಕೋಡ್ ಕಳಿಸಿ.",
    "ta": "உங்கள் 6 இலக்க பின் கோடை அனுப்புங்கள்.",
    "te": "మీ 6-అంకెల పిన్ కోడ్ పంపండి.",
    "mr": "कृपया तुमचा 6-अंकी पिन कोड पाठवा.",
    "pa": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ 6-ਅੰਕ ਦਾ ਪਿਨ ਕੋਡ ਭੇਜੋ।",
}

# In-memory session store keyed by phone-number hash (sufficient for demo).
_sessions: dict[str, dict] = {}


def _extract_text(payload: dict) -> str:
    """Pull the message text out of a Green-API incoming webhook body."""
    md = payload.get("messageData", {}) or {}
    # textMessage and extendedTextMessage are the common shapes
    tm = md.get("textMessageData", {}) or {}
    if tm.get("textMessage"):
        return tm["textMessage"].strip()
    ext = md.get("extendedTextMessageData", {}) or {}
    if ext.get("text"):
        return ext["text"].strip()
    return ""


def _sender_chat_id(payload: dict) -> str:
    sd = payload.get("senderData", {}) or {}
    return sd.get("chatId", "")


async def _send_message(chat_id: str, text: str):
    """Send a WhatsApp reply via Green-API."""
    if not (ID_INSTANCE and API_TOKEN):
        print("Green-API not configured; cannot send.")
        return
    url = f"{BASE}/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json={"chatId": chat_id, "message": text})
    except Exception as e:
        print(f"Green-API send error: {e}")


async def handle_greenapi_webhook(payload: dict, pipeline) -> dict:
    """Process one Green-API webhook. Replies out-of-band via _send_message.
    Returns a small JSON ack for the HTTP response (Green-API ignores the body)."""
    # Only act on incoming text messages
    if payload.get("typeWebhook") != "incomingMessageReceived":
        return {"status": "ignored", "reason": "not an incoming message"}

    chat_id = _sender_chat_id(payload)
    body = _extract_text(payload)
    if not chat_id:
        return {"status": "ignored", "reason": "no chatId"}

    phone_hash = hashlib.sha256(chat_id.encode()).hexdigest()[:16]
    session = _sessions.get(phone_hash, {})

    # ── Onboarding: language ──
    if "language" not in session:
        if body in LANG_MAP:
            session["language"] = LANG_MAP[body]
            _sessions[phone_hash] = session
            await _send_message(chat_id, PINCODE_PROMPT.get(session["language"], PINCODE_PROMPT["en"]))
        else:
            await _send_message(chat_id, ONBOARDING_MSG)
        return {"status": "ok"}

    # ── Onboarding: pincode ──
    if "pincode" not in session:
        if body.isdigit() and len(body) == 6:
            session["pincode"] = body
            _sessions[phone_hash] = session
            lang = session["language"]
            confirm = {
                "en": f"Got it! Pincode {body} set. Now ask me anything about farming! 🌾",
                "hi": f"ठीक है! पिन कोड {body} सेट हो गया। अब खेती के बारे में कोई भी सवाल पूछें! 🌾",
                "kn": f"ಸರಿ! ಪಿನ್ ಕೋಡ್ {body} ಸೆಟ್ ಆಗಿದೆ. ಈಗ ಕೃಷಿ ಪ್ರಶ್ನೆ ಕೇಳಿ! 🌾",
            }
            await _send_message(chat_id, confirm.get(lang, confirm["en"]))
        else:
            await _send_message(chat_id, "Please send a valid 6-digit PIN code.")
        return {"status": "ok"}

    # ── Normal query ──
    try:
        result = await pipeline.query(
            message=body,
            language=session["language"],
            pincode=session.get("pincode"),
        )
        reply = result["response"]
        if result.get("sources"):
            top = result["sources"][0]
            reply += f"\n\n📄 Source: {top['title']} ({top['state']})"
    except Exception as e:
        print(f"Green-API query error: {e}")
        reply = "Sorry, I'm having trouble right now. Please try again in a moment."

    await _send_message(chat_id, reply)
    return {"status": "ok"}
