import os, base64
import httpx

BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_BASE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

BHASHINI_LANG_CODES = {
    "en": "en", "hi": "hi", "kn": "kn", "ta": "ta",
    "te": "te", "mr": "mr", "gu": "gu", "pa": "pa",
}


async def transcribe_audio(audio_bytes: bytes, language: str):
    """Convert audio bytes to text using Bhashini ASR."""
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None

    audio_b64 = base64.b64encode(audio_bytes).decode()
    lang_code = BHASHINI_LANG_CODES.get(language, "hi")

    payload = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": lang_code},
                "audioFormat": "ogg",
                "samplingRate": 16000,
            }
        }],
        "inputData": {"audio": [{"audioContent": audio_b64}]}
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BHASHINI_BASE_URL, json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            return data["pipelineResponse"][0]["output"][0]["source"]
    except Exception as e:
        print(f"Bhashini ASR error: {e}")
        return None


async def translate_text(text: str, source_lang: str, target_lang: str):
    """Translate text using Bhashini."""
    if source_lang == target_lang:
        return text
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None

    payload = {
        "pipelineTasks": [{
            "taskType": "translation",
            "config": {
                "language": {
                    "sourceLanguage": BHASHINI_LANG_CODES.get(source_lang, "en"),
                    "targetLanguage": BHASHINI_LANG_CODES.get(target_lang, "hi"),
                }
            }
        }],
        "inputData": {"input": [{"source": text}]}
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BHASHINI_BASE_URL, json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            return data["pipelineResponse"][0]["output"][0]["target"]
    except Exception as e:
        print(f"Bhashini translation error: {e}")
        return None


async def synthesize_speech(text: str, language: str):
    """Convert text to speech using Bhashini TTS. Returns audio bytes."""
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None

    lang_code = BHASHINI_LANG_CODES.get(language, "hi")
    payload = {
        "pipelineTasks": [{
            "taskType": "tts",
            "config": {
                "language": {"sourceLanguage": lang_code},
                "gender": "female",
                "samplingRate": 8000,
            }
        }],
        "inputData": {"input": [{"source": text}]}
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                BHASHINI_BASE_URL, json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            audio_b64 = data["pipelineResponse"][0]["audio"][0]["audioContent"]
            return base64.b64decode(audio_b64)
    except Exception as e:
        print(f"Bhashini TTS error: {e}")
        return None
