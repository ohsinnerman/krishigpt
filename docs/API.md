# KrishiGPT — API Reference

Base URL (dev): `http://localhost:8000`  
Base URL (prod): `https://api.krishigpt.app`

All endpoints return JSON. All POST bodies are JSON. No authentication required for MVP (rate-limited by IP).

---

## POST /chat

Primary endpoint. Takes a farmer question and returns an AI-generated answer with source attribution.

### Request

```json
{
  "message": "ಭತ್ತದ ಬೆಳೆಯಲ್ಲಿ ಕಾಂಡ ಕೊರೆಯುವ ಹುಳದ ನಿಯಂತ್ರಣ ಹೇಗೆ?",
  "language": "kn",
  "pincode": "560001",
  "session_id": "optional-uuid-for-continuity"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | Farmer's question in any supported language |
| `language` | string | No | ISO 639-1 code. Default: `"en"`. Auto-detected if not provided |
| `pincode` | string | No | 6-digit Indian PIN code for region filtering |
| `session_id` | string | No | UUID for multi-turn continuity (web only) |

### Response

```json
{
  "response": "ಭತ್ತದ ಕಾಂಡ ಕೊರೆಯುವ ಹುಳ ನಿಯಂತ್ರಿಸಲು ಕ್ಲೋರ್ಪೈರಿಫಾಸ್ 20 EC @ 2 ml/l ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ...",
  "sources": [
    {
      "title": "ICAR Package of Practices for Paddy",
      "state": "Karnataka",
      "topic": "pest",
      "score": 0.847
    },
    {
      "title": "KVK Bengaluru Pest Management Booklet",
      "state": "Karnataka",
      "topic": "pest",
      "score": 0.791
    }
  ],
  "region": "Bengaluru Urban, Karnataka",
  "language": "kn",
  "latency_ms": 3241
}
```

| Field | Type | Description |
|---|---|---|
| `response` | string | AI-generated answer in requested language |
| `sources` | array | Top retrieved documents with relevance scores |
| `sources[].title` | string | Document title |
| `sources[].state` | string | State scope of document, or "pan-india" |
| `sources[].topic` | string | Topic category |
| `sources[].score` | float | Relevance score (0–1, higher is more relevant) |
| `region` | string | Resolved region from pincode, or null |
| `language` | string | Language used in response |
| `latency_ms` | int | Total processing time in milliseconds |

### Error Responses

```json
// 422 Validation Error
{
  "detail": [{"loc": ["body", "message"], "msg": "field required"}]
}

// 500 Internal Server Error
{
  "detail": "Gemini API rate limit exceeded. Please retry in 60 seconds."
}
```

### Example Queries (for testing)

```bash
# English — pest question with pincode
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I control stem borer in paddy?", "language": "en", "pincode": "560001"}'

# Hindi — fertilizer question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "गेहूं में यूरिया कब और कितना डालें?", "language": "hi", "pincode": "208001"}'

# Tamil — scheme question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "PMFBY காப்பீட்டு திட்டத்தில் எப்படி பதிவு செய்வது?", "language": "ta", "pincode": "600001"}'

# Telugu — disease question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "వరి పంటలో వెన్ను తెగులు నివారణ చేయడం ఎలా?", "language": "te", "pincode": "500001"}'
```

---

## GET /health

Health check. Returns index status.

### Response

```json
{
  "status": "ok",
  "chunks_loaded": 24183,
  "index_size_mb": 35.7,
  "model": "paraphrase-multilingual-MiniLM-L12-v2",
  "generator": "gemini-1.5-flash",
  "uptime_seconds": 3600
}
```

---

## GET /languages

Returns list of supported languages.

### Response

```json
{
  "supported": [
    {"code": "en", "name": "English"},
    {"code": "hi", "name": "हिन्दी"},
    {"code": "kn", "name": "ಕನ್ನಡ"},
    {"code": "ta", "name": "தமிழ்"},
    {"code": "te", "name": "తెలుగు"},
    {"code": "mr", "name": "मराठी"},
    {"code": "gu", "name": "ગુજરાતી"},
    {"code": "pa", "name": "ਪੰਜਾਬੀ"}
  ]
}
```

---

## GET /pincode/{pincode}

Resolves a 6-digit PIN code to region metadata.

### Response

```json
{
  "pincode": "560001",
  "district": "Bengaluru Urban",
  "state": "Karnataka",
  "agro_zone": "Deccan-South",
  "division": "Bengaluru"
}
```

### Error

```json
// 404
{"detail": "Pincode not found"}
```

---

## POST /webhook/whatsapp

Twilio webhook endpoint. Receives incoming WhatsApp messages (text, voice, image).  
**Validates `X-Twilio-Signature` header. Reject all unsigned requests.**

### Request (Twilio POST form data)

```
From=whatsapp:+919876543210
Body=ಭತ್ತದಲ್ಲಿ ರೋಗ ಬಂದಿದೆ
MessageSid=SMxxxx
NumMedia=0
```

For voice notes:
```
From=whatsapp:+919876543210
Body=
NumMedia=1
MediaUrl0=https://api.twilio.com/2010-04-01/Accounts/.../Messages/.../Media/...
MediaContentType0=audio/ogg
```

### Response (TwiML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>ಭತ್ತದ ರೋಗ ನಿಯಂತ್ರಣಕ್ಕೆ...</Message>
</Response>
```

---

## POST /feedback

Logs farmer feedback on a response.

### Request

```json
{
  "message_id": "uuid-of-assistant-message",
  "feedback": 1
}
```

| `feedback` | Meaning |
|---|---|
| `1` | 👍 Helpful |
| `-1` | 👎 Not helpful |

### Response

```json
{"status": "recorded"}
```

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| `POST /chat` | 10 requests/minute per IP |
| `POST /webhook/whatsapp` | 10 messages/hour per phone number |
| All other endpoints | 60 requests/minute per IP |

Rate limit response:
```json
// HTTP 429
{"detail": "Rate limit exceeded. Try again in 45 seconds."}
```
