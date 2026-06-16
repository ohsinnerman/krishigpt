import os, time
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from rag.pipeline import KrishiGPTPipeline

limiter = Limiter(key_func=get_remote_address)
pipeline: Optional[KrishiGPTPipeline] = None

RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "10")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    pipeline = KrishiGPTPipeline()
    yield


app = FastAPI(title="KrishiGPT", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    pincode: Optional[str] = None
    session_id: Optional[str] = None
    region_filter: bool = True


class SourceDoc(BaseModel):
    title: str
    state: str
    topic: str
    score: float


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceDoc]
    region: Optional[str]
    language: str
    latency_ms: int
    cache_hit: bool = False


# ── Routes ──────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def chat(req: ChatRequest, request: Request):
    t0 = time.monotonic()
    try:
        result = await pipeline.query(
            message=req.message,
            language=req.language,
            pincode=req.pincode,
            session_id=req.session_id,
            region_filter=req.region_filter,
        )
        result["latency_ms"] = int((time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        # Log the real traceback so demo-time failures are diagnosable, but
        # return a friendly fallback (200) instead of a raw 500 to the user.
        import traceback
        traceback.print_exc()
        return {
            "response": "Sorry, I'm having trouble answering right now. Please try again in a moment.",
            "sources": [],
            "region": None,
            "language": req.language,
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "cache_hit": False,
        }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "chunks_loaded": len(pipeline.chunks) if pipeline else 0,
        "model": os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"),
        "generator": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "gemini_configured": bool(os.getenv("GOOGLE_API_KEY", "").strip()),
    }


@app.get("/languages")
async def languages():
    return {"supported": [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
        {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
        {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
        {"code": "te", "name": "Telugu", "native": "తెలుగు"},
        {"code": "mr", "name": "Marathi", "native": "मराठी"},
        {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
        {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    ]}


@app.get("/pincode/{pincode}")
async def resolve_pincode(pincode: str):
    from data.pincode_mapper import get_region_from_pincode
    info = get_region_from_pincode(pincode)
    if not info:
        raise HTTPException(404, "Pincode not found")
    return info


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    from integrations.whatsapp import handle_whatsapp_message
    form_data = await request.form()
    return await handle_whatsapp_message(dict(form_data), pipeline)


@app.post("/webhook/greenapi")
async def greenapi_webhook(request: Request):
    from integrations.greenapi import handle_greenapi_webhook
    payload = await request.json()
    return await handle_greenapi_webhook(payload, pipeline)


@app.post("/feedback")
async def feedback(message_id: str, score: int):
    # score: 1 = helpful, -1 = not helpful
    return {"status": "recorded"}
