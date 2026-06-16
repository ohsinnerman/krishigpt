import os, hashlib
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
import httpx

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

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

# In-memory session store (sufficient for demo)
_sessions = {}


async def handle_whatsapp_message(form_data: dict, pipeline) -> Response:
    from_number = form_data.get("From", "")
    body = (form_data.get("Body", "") or "").strip()
    num_media = int(form_data.get("NumMedia", 0) or 0)

    phone_hash = hashlib.sha256(from_number.encode()).hexdigest()[:16]
    session = _sessions.get(phone_hash, {})

    resp = MessagingResponse()

    # ── Voice note ────────────────────────────────────────────────────────────
    if num_media > 0 and not body:
        media_url = form_data.get("MediaUrl0", "")
        media_type = form_data.get("MediaContentType0", "")
        if "audio" in media_type:
            body = await _transcribe_audio(media_url, session.get("language", "hi"))
            if not body:
                resp.message("Sorry, I couldn't understand the audio. Please type your question.")
                return Response(content=str(resp), media_type="text/xml")

    # ── Onboarding: language ──────────────────────────────────────────────────
    if "language" not in session:
        if body in LANG_MAP:
            session["language"] = LANG_MAP[body]
            _sessions[phone_hash] = session
            resp.message(PINCODE_PROMPT.get(session["language"], PINCODE_PROMPT["en"]))
        else:
            resp.message(ONBOARDING_MSG)
        return Response(content=str(resp), media_type="text/xml")

    # ── Onboarding: pincode ───────────────────────────────────────────────────
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
            resp.message(confirm.get(lang, confirm["en"]))
        else:
            resp.message("Please send a valid 6-digit PIN code.")
        return Response(content=str(resp), media_type="text/xml")

    # ── Normal query ──────────────────────────────────────────────────────────
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
    except Exception:
        reply = "Sorry, I'm having trouble right now. Please try again in a moment."

    resp.message(reply)
    return Response(content=str(resp), media_type="text/xml")


async def _transcribe_audio(media_url: str, language: str):
    from integrations.bhashini import transcribe_audio
    try:
        audio = await _download_audio(media_url)
        if audio:
            return await transcribe_audio(audio, language)
    except Exception as e:
        print(f"ASR error: {e}")
    return None


async def _download_audio(url: str):
    try:
        auth = (os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", ""))
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=auth, timeout=10)
            return resp.content if resp.status_code == 200 else None
    except Exception:
        return None
