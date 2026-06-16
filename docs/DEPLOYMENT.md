# KrishiGPT — Deployment Guide

---

## 1. Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker Desktop
- `git`

### Steps

```bash
# Clone
git clone https://github.com/yourname/krishigpt
cd krishigpt

# Python env
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Node deps
cd frontend && npm install && cd ..

# Environment
cp .env.example .env
# Edit .env and fill in GOOGLE_API_KEY, BHASHINI_USER_ID, BHASHINI_API_KEY

# Infra (Postgres + Redis)
docker-compose up -d postgres redis

# Build FAISS index (first time only, ~20 min)
bash scripts/download_corpus.sh
python scripts/build_index.py

# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend && npm run dev
```

---

## 2. Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./backend/data:/app/data      # FAISS index persistence
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: krishigpt
      POSTGRES_USER: krishigpt
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

```bash
# Start everything
docker-compose up --build

# Rebuild just backend after code changes
docker-compose up --build backend
```

---

## 3. Production Deployment (Railway)

Railway is recommended for the MVP — free tier covers this workload.

### Steps

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Initialize project
railway init

# Create services
railway service create backend
railway service create frontend

# Add databases
railway add --database postgresql
railway add --database redis

# Set environment variables
railway variables set GOOGLE_API_KEY=your_key
railway variables set BHASHINI_USER_ID=your_id
railway variables set BHASHINI_API_KEY=your_key
railway variables set TWILIO_ACCOUNT_SID=your_sid
railway variables set TWILIO_AUTH_TOKEN=your_token

# Deploy
railway up
```

### Railway Procfile for backend
```
# backend/Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

### Railway Procfile for frontend
```
# frontend/Procfile
web: npm run start
```

**Important:** The FAISS index (data/faiss.index + data/chunks.pkl) must be built before deployment. Options:
1. Commit the built index to git (if < 100MB) — simplest
2. Build in a Railway startup script (slow, don't do this)
3. Store on Railway persistent volumes (recommended for production)

---

## 4. Render Deployment (Alternative)

```yaml
# render.yaml
services:
  - type: web
    name: krishigpt-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: BHASHINI_API_KEY
        sync: false
    disk:
      name: faiss-index
      mountPath: /app/data
      sizeGB: 1

  - type: web
    name: krishigpt-frontend
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm run start
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: https://krishigpt-backend.onrender.com
```

---

## 5. Twilio WhatsApp Setup

1. Create a Twilio account (free trial gives $15 credit)
2. Activate the WhatsApp Sandbox: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
3. Set webhook URL: `https://your-domain.com/webhook/whatsapp`
4. Twilio will send `POST` with form data to this URL
5. For local testing, use ngrok:
   ```bash
   ngrok http 8000
   # Copy HTTPS URL and set in Twilio console
   ```

**WhatsApp Business API (for production — after demo):**
- Apply through Meta (2-3 weeks approval)
- Or use Twilio Business Profile (faster)
- Cost: Twilio charges per conversation (check current pricing)

---

## 6. Bhashini Setup

1. Register: https://bhashini.gov.in/
2. Create a project in the Bhashini Developer Console
3. Note down: `userID` and `ulcaApiKey`
4. Test with:
```bash
curl -X POST https://dhruva-api.bhashini.gov.in/services/inference/pipeline \
  -H "userID: YOUR_USER_ID" \
  -H "ulcaApiKey: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": "hi"}}}],
    "inputData": {"audio": [{"audioContent": "BASE64_AUDIO_HERE"}]}
  }'
```

---

## 7. Environment Variables Reference

```bash
# .env.example

# Required
GOOGLE_API_KEY=               # Gemini 1.5 Flash — console.cloud.google.com
BHASHINI_USER_ID=             # bhashini.gov.in developer portal
BHASHINI_API_KEY=             # same as above

# Database
DATABASE_URL=postgresql://krishigpt:password@localhost:5432/krishigpt
REDIS_URL=redis://localhost:6379/0
POSTGRES_PASSWORD=your_secure_password

# WhatsApp (optional for MVP)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Config
RAG_TOP_K=5                   # Number of chunks to retrieve
REGION_BOOST_EXACT=0.20       # Score boost for exact state match
REGION_BOOST_ZONE=0.10        # Score boost for same agro-climatic zone
REGION_BOOST_PAN_INDIA=0.05   # Score boost for pan-india docs
CACHE_TTL_SECONDS=3600        # Query cache TTL
SESSION_TTL_HOURS=24          # WhatsApp session TTL
RATE_LIMIT_PER_MINUTE=10      # API rate limit per IP
MAX_TOKENS_OUTPUT=500          # Max tokens in Gemini response

# Model paths (change if using different models)
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
FAISS_INDEX_PATH=data/faiss.index
CHUNKS_PATH=data/chunks.pkl
PINCODE_DB_PATH=data/pincodes.csv

# Environment
ENVIRONMENT=development       # development | production
LOG_LEVEL=INFO
```

---

## 8. Monitoring (Optional but Recommended)

```python
# Simple logging setup in main.py
import structlog
log = structlog.get_logger()

# Log every query (no PII)
log.info("chat_query",
    language=req.language,
    state=result["region"],
    latency_ms=result["latency_ms"],
    source_count=len(result["sources"]),
    cache_hit=result.get("cache_hit", False),
)
```

Use Railway's built-in log streaming for MVP. Add Datadog/Grafana for v1.

---

## 9. Checklist Before Going Live

- [ ] All API keys in environment variables (zero in source code)
- [ ] `ENVIRONMENT=production` set
- [ ] Twilio webhook signature validation enabled
- [ ] Rate limiting enabled
- [ ] PostgreSQL with persistent volume (not ephemeral)
- [ ] Redis with persistent volume
- [ ] FAISS index loaded at startup (check `/health` endpoint)
- [ ] Health check endpoint returning 200
- [ ] Test all 7 languages manually
- [ ] Test voice note flow on WhatsApp sandbox
- [ ] README updated with live URL
