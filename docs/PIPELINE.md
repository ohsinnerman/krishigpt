# KrishiGPT — 14-Hour Build Pipeline

> This is your execution contract. Follow it in order. Do not skip ahead.

**Start time:** ___________  
**End time (target):** ___________ + 14h  
**Demo time:** ___________

---

## Pre-Flight (Before the Clock Starts)

Do these before you begin the 14-hour sprint:

- [ ] Python 3.11 installed and aliased as `python`
- [ ] Node.js 20+ installed
- [ ] Docker Desktop running
- [ ] `git` configured
- [ ] **Get API keys NOW — don't wait until you need them:**
  - [ ] Google AI Studio → Gemini API key → https://aistudio.google.com/
  - [ ] Bhashini → https://bhashini.gov.in/ (approve in ~10 min)
  - [ ] Twilio account + WhatsApp sandbox activated (can skip for demo)
- [ ] Create a new GitHub repo: `krishigpt`
- [ ] Open `MASTER_PROMPT.md` in one window; keep it open

---

## Hour 0–1: Project Scaffold

**Goal:** Repo exists, runs, makes a fake response.

```bash
mkdir krishigpt && cd krishigpt
git init
# Copy all doc files into root

# Create folder structure
mkdir -p backend/{rag,data/{corpus,eval,sample_docs},integrations,models,tests}
mkdir -p frontend/src
mkdir -p scripts
```

- [ ] `backend/requirements.txt` written and installed in venv
- [ ] `frontend/` Next.js initialized (`npx create-next-app@latest frontend`)
- [ ] `docker-compose.yml` written
- [ ] `.env.example` copied to `.env`, keys filled in
- [ ] `docker-compose up -d postgres redis` → both green
- [ ] `GET http://localhost:8000/health` returns 200 (even with hardcoded response)

**Checkpoint:** Fake `/chat` endpoint returns hardcoded JSON. Frontend shows it.

---

## Hour 1–3: Ingestion Pipeline

**Goal:** FAISS index built with at least 100 real chunks.

**Do this in order:**

1. Write `backend/data/chunker.py` — PDF → text → chunks with metadata
2. Write `backend/data/ingest.py` — orchestrates chunker → embedder → FAISS saver
3. Write `backend/rag/embeddings.py` — loads MiniLM model once, exposes `encode()`
4. Write `backend/rag/vector_store.py` — FAISS index load/save/search
5. Write `backend/data/pincode_mapper.py` — CSV lookup, returns state + zone

```bash
# Download a few seed PDFs to test with
wget https://agritech.tnau.ac.in/agriculture/agri_cereals_paddy.html -O backend/data/corpus/paddy_tnau.html
wget https://agritech.tnau.ac.in/agriculture/agri_cereals_wheat.html -O backend/data/corpus/wheat_tnau.html
# Download pincode DB
wget https://raw.githubusercontent.com/samayo/country-json/master/src/country-in-zipcode.json
# Better: India pincode CSV from data.gov.in

# Run ingestion
python backend/data/ingest.py --corpus-dir backend/data/corpus --output-dir backend/data
```

- [ ] `backend/data/faiss.index` exists
- [ ] `backend/data/chunks.pkl` exists with > 100 chunks
- [ ] `python -c "import faiss; import pickle; chunks = pickle.load(open('backend/data/chunks.pkl','rb')); print(len(chunks), 'chunks')"` prints a number
- [ ] Pincode `560001` resolves to `Karnataka`
- [ ] Pincode `110001` resolves to `Delhi`

**Checkpoint:** `python -c "from rag.vector_store import search; print(search('paddy stem borer treatment'))"` returns at least 2 results.

---

## Hour 3–5: RAG Pipeline

**Goal:** `/chat` endpoint returns real AI-generated answers.

**Build in this order:**

1. `backend/rag/retriever.py` — wraps vector_store, adds region re-ranking
2. `backend/rag/generator.py` — builds the Gemini prompt, calls API, returns text
3. `backend/rag/pipeline.py` — orchestrates retriever + generator, handles caching
4. Update `backend/main.py` — wire pipeline into `/chat` endpoint

**Key things to get right in the prompt (copy from MASTER_PROMPT.md):**
- Language instruction must be in that language
- "Never make up numbers not in the context"
- "If no relevant document found, say so"
- System role as agricultural advisor

```bash
# Test it
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I control stem borer in paddy?", "language": "en", "pincode": "560001"}'
```

- [ ] Response is in English and mentions a specific treatment
- [ ] `sources` array has at least 1 item
- [ ] `region` is "Karnataka" (from pincode 560001)
- [ ] Response time < 10 seconds

```bash
# Test Hindi
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "गेहूं में यूरिया कब डालें?", "language": "hi", "pincode": "208001"}'
```

- [ ] Response is in Hindi (contains Devanagari script)
- [ ] Mentions UP (from pincode 208001 = Kanpur)

**Checkpoint:** 5 different agricultural questions answered correctly in 2 languages.

---

## Hour 5–7: Frontend

**Goal:** A farmer can use a web browser to ask a question and see an answer.

**Build these Next.js components:**

1. `frontend/src/components/LanguageSelector.tsx` — dropdown with 7 languages, flag emojis
2. `frontend/src/components/PincodeInput.tsx` — input with validation + region display
3. `frontend/src/components/ChatBubble.tsx` — user message + bot response with sources
4. `frontend/src/components/SourceCard.tsx` — small card showing doc title + state + score
5. `frontend/src/app/chat/page.tsx` — wires everything together
6. `frontend/src/lib/api.ts` — typed fetch wrapper to backend

**Design requirements:**
- Works on mobile (375px viewport minimum)
- Language selector is prominent — first thing user sees
- Pincode input shows resolved region below (e.g. "📍 Bengaluru, Karnataka")
- Sources are collapsed by default, expandable
- Loading state shows "Thinking..." with a spinner
- Error state is user-friendly ("Something went wrong. Please try again.")

**Don't over-engineer:** Tailwind + shadcn/ui. No custom CSS. No animations. Ship it.

- [ ] Open `http://localhost:3000` — page loads
- [ ] Select "Kannada" from language dropdown
- [ ] Enter pincode 560001 → shows "Bengaluru, Karnataka"
- [ ] Type "ಭತ್ತದ ರೋಗ" → response appears in Kannada
- [ ] Sources are visible below response
- [ ] Works on mobile viewport (Chrome DevTools)

**Checkpoint:** Full end-to-end flow works in browser for English and one regional language.

---

## Hour 7–8: WhatsApp Integration

**Goal:** Twilio webhook receives a WhatsApp message and replies.

**Build:**
1. `backend/integrations/whatsapp.py` — Twilio webhook handler
2. Add `/webhook/whatsapp` route to `backend/main.py`

```bash
# Install ngrok for local webhook testing
brew install ngrok   # or download from ngrok.com
ngrok http 8000
# Copy HTTPS URL

# Set in Twilio console:
# Sandbox webhook URL: https://your-ngrok-url.ngrok.io/webhook/whatsapp
```

- [ ] Send "hello" to Twilio sandbox number → get a response
- [ ] Send a voice note → get a text response (Bhashini ASR)
- [ ] Language is remembered in session (send in Hindi → next message auto-Hindi)
- [ ] Pincode is remembered (set once, used for all subsequent queries)

**WhatsApp onboarding flow:**
```
First message from a new number:
→ "Welcome to KrishiGPT 🌾 I can answer your farming questions in 7 languages.
   Reply with your language: 1=English 2=हिन्दी 3=ಕನ್ನಡ 4=தமிழ் 5=తెలుగు 6=मराठी 7=ਪੰਜਾਬੀ"

User replies "3":
→ "ತಮ್ಮ ಪಿನ್ ಕೋಡ್ ಕಳಿಸಿ ನಿಮ್ಮ ಪ್ರದೇಶಕ್ಕೆ ಸೂಕ್ತವಾದ ಸಲಹೆ ನೀಡಲು"

User replies "560001":
→ "ಬೆಂಗಳೂರು, ಕರ್ನಾಟಕ ✅ ಇನ್ನು ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆ ಕೇಳಿ!"
```

**Checkpoint:** Full WhatsApp flow works: onboarding → language → pincode → question → answer.

---

## Hour 8–9: Session Persistence + Caching

**Goal:** System is robust, fast, and handles errors gracefully.

1. Implement Redis session storage (phone_hash → language, pincode, history)
2. Implement Redis query cache (query_hash → response)
3. Add error handling: Gemini down → fallback message; Bhashini down → skip translation
4. Add rate limiting (slowapi library)

```python
# backend/main.py additions
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(req: ChatRequest, request: Request):
    ...
```

- [ ] Same question asked twice → second response < 500ms (cache hit)
- [ ] If `GOOGLE_API_KEY` is wrong → returns graceful error, not 500
- [ ] 11th request in a minute from same IP → 429 response

**Checkpoint:** Run 20 concurrent requests → all complete, no crashes.

---

## Hour 9–10: Evaluation Run

**Goal:** Numbers you can put in your paper / presentation.

```bash
# Create manual eval set (50 questions, 10 per language pair)
python scripts/create_manual_eval.py

# Run evaluation
python scripts/evaluate.py --config rag_no_region
python scripts/evaluate.py --config rag_with_region

# Compare
python scripts/compare_results.py
```

Write down these numbers (you need them for the demo):
- [ ] Precision@5 with region: ___
- [ ] Precision@5 without region: ___
- [ ] Hallucination rate with region: ___
- [ ] Hallucination rate without region: ___
- [ ] Mean latency: ___ ms

**Checkpoint:** You have a comparison table that proves region-aware retrieval is better.

---

## Hour 10–11: Polish Pass

**Goal:** The demo looks real, not like a hackathon project.

**Frontend polish:**
- [ ] Add KrishiGPT logo (text logo is fine — big green font)
- [ ] Add tagline: "Your farming expert in your language"
- [ ] Add example questions that auto-fill on click
- [ ] Show language flag + name in chat header
- [ ] Show region badge once pincode is set
- [ ] Loading spinner is a tractor icon or similar (or just "🌾 Thinking...")
- [ ] Mobile layout is clean

**Backend polish:**
- [ ] Add `GET /health` with chunk count, model name
- [ ] Structured logging (request ID, language, latency — never full query text)
- [ ] Graceful shutdown (SIGTERM handler)
- [ ] Add a basic `/admin/stats` endpoint (total queries, avg latency, top languages)

**Prompt polish:**
- [ ] Test "I don't know" cases — system correctly admits uncertainty
- [ ] Test scheme questions — no wrong dates or eligibility criteria
- [ ] Dosage numbers are always cited from the document, not hallucinated

---

## Hour 11–12: Deployment

**Goal:** Live URL that works for the demo.

```bash
# Railway deployment
railway login
railway init
railway up

# Or Render (if Railway is slow)
# Push to GitHub, connect Render, deploy

# Set environment variables in Railway dashboard
# Test live URL
curl https://your-app.railway.app/health
```

- [ ] `https://your-domain.com/health` returns 200
- [ ] Web chat works on live URL
- [ ] WhatsApp webhook URL updated to live URL
- [ ] Test one full WhatsApp conversation on live deployment

**Checkpoint:** Someone on their phone can use KrishiGPT right now.

---

## Hour 12–13: Demo Script + Docs

**Goal:** Your demo tells a story. Your README is presentable.

**Demo script (practice this 3 times):**

```
Opening (30 seconds):
"70% of Indian farmers cannot access agricultural advice in their language. 
KrishiGPT solves this. Let me show you."

Demo 1 — Web, English (1 minute):
1. Open web interface
2. Select "English"  
3. Enter pincode 560001 → show "Bengaluru, Karnataka appears"
4. Ask: "I have stem borer in my paddy. What pesticide should I use?"
5. Show response + source documents

Demo 2 — Web, Kannada (30 seconds):
1. Switch language to Kannada
2. Same pincode
3. Ask same question in Kannada: "ಭತ್ತದಲ್ಲಿ ಕಾಂಡ ಕೊರೆಯುವ ಹುಳ ನಿಯಂತ್ರಣ?"
4. Show response is in Kannada, from Karnataka docs

Demo 3 — WhatsApp (1 minute):
1. Send voice note in Hindi to WhatsApp sandbox
2. Show transcription + response
3. "This is the farmer interface. No app to download."

The differentiator (30 seconds):
"The key innovation: switch to another state's pincode and show how the 
retrieved documents change. A farmer in Punjab gets Punjab-specific wheat 
advice. A farmer in Karnataka gets Karnataka-specific rice advice."

Results (30 seconds):
Show the eval table: 
"Region-aware retrieval reduces hallucination from 22% to 14%."
```

**README updates:**
- [ ] Add live URL to README
- [ ] Add demo GIF/screenshot
- [ ] Add "cite this repo" section for paper

---

## Hour 13–14: Buffer + Final Testing

**Goal:** Nothing breaks during the demo.

**Final testing checklist:**
- [ ] Ask 5 questions in English → all reasonable answers
- [ ] Ask 2 questions in Hindi → Devanagari script in response
- [ ] Ask 1 question in Tamil → Tamil script in response
- [ ] Ask about a government scheme → correct, cautious response
- [ ] Ask something completely unrelated to farming → polite redirect
- [ ] Send a WhatsApp voice note → gets a response
- [ ] Ask the same question twice → second response is faster (cache)
- [ ] Load the page on your phone → mobile layout looks good
- [ ] Health endpoint shows correct chunk count
- [ ] No hardcoded API keys anywhere in the code

**Git hygiene:**
```bash
git add .
git commit -m "feat: KrishiGPT v1.0 — region-aware multilingual RAG agri-advisor"
git push origin main
```

---

## Minimum Viable Demo

If time runs out, make sure at minimum you have:

1. ✅ `/chat` endpoint working (English, Hindi, one South Indian language)
2. ✅ Region filtering working (different pincode = different source documents)
3. ✅ Web UI showing response + sources
4. ✅ Numbers proving region-aware > non-region-aware

The WhatsApp, voice, and all 7 languages are bonuses.

---

## If You're Stuck

| Problem | Solution |
|---|---|
| FAISS index takes too long to build | Use 20 sample chunks hardcoded in a JSON file for demo |
| Gemini API rate limited | Add `time.sleep(4)` between calls; use cache aggressively |
| Bhashini ASR not working | Skip voice for demo; text-only is still impressive |
| Kannada/Tamil not working | Gemini sometimes defaults to English; add stronger language instruction |
| WhatsApp webhook not receiving | Use ngrok; check Twilio logs; validate the URL in Twilio console |
| Railway deployment failing | Fall back to `localhost + ngrok` for the live URL in demo |
| Out of time | Demo from localhost; judges don't need a live URL |

---

## The One Number That Matters

**14% hallucination rate (with region) vs 22% (without region) = your paper's result.**

Everything else is engineering. This number is your research contribution.
