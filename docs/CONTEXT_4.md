# CONTEXT_4.md — KrishiGPT (checkpoint 4): WhatsApp live + Demo Runbook

> Read CONTEXT.md → 2 → 3 → this. This is the final checkpoint: WhatsApp (Green-API)
> working end-to-end, plus the **demo runbook for the presentation**.
> Last updated: 2026-06-17.

---

## All 7 build phases complete ✅

| Phase | Status |
|---|---|
| 0 Scaffold | ✅ |
| 1 Ingestion (FAISS, pincode) | ✅ |
| 2 RAG pipeline (Gemini 2.5-flash) | ✅ live |
| Corpus (45 chunks / 12 states) | ✅ |
| 3 Frontend (Next.js 16) | ✅ end-to-end |
| Provider failover (Gemini→Groq) | ✅ |
| 4 Evaluation | ✅ Top-1 56%→100%, MRR 0.66→1.0, halluc 20%→0% |
| 5 Polish | ✅ 7 langs, doc-leak fixed, off-topic handling, branding |
| 6 WhatsApp (Green-API) | ✅ **live end-to-end** |
| 7 Buffer / runbook | ✅ this doc |

---

## WhatsApp via Green-API (working)

We used **Green-API** instead of Twilio (Twilio dashboard was down). Unlike Twilio's
synchronous TwiML, Green-API POSTs incoming messages as JSON to our webhook, and we reply
with a separate `sendMessage` API call. Code: `backend/integrations/greenapi.py`,
route `POST /webhook/greenapi` in `main.py`.

**Numbers in this setup:**
- **Bot number** (connected to the Green-API instance): `918160407939`. Receives farmer
  messages and sends replies.
- **Farmer** messages the bot from any WhatsApp number; the handler always replies to the
  *sender's* `chatId` (read from the webhook payload).

**Verified working:** ngrok HTTP log showed real `POST /webhook/greenapi → 200 OK` from
live WhatsApp messages; replies delivered (Green-API returns an `idMessage`).

### To bring WhatsApp back up before the demo
1. **Backend running** (see run commands below), from `backend/`.
2. **ngrok** in its own terminal: `ngrok http 8000`
   - Free ngrok URLs **change on every restart**. If the URL is no longer
     `https://terrence-drastic-conor.ngrok-free.dev`, update the Green-API webhook (step 3).
3. **Green-API webhook URL** = `https://<your-ngrok>.ngrok-free.dev/webhook/greenapi`
   - Set in the Green-API console, or via API:
     `POST https://api.green-api.com/waInstance<ID>/setSettings/<TOKEN>`
     body `{"webhookUrl":"https://<ngrok>/webhook/greenapi","incomingWebhook":"yes"}`
   - Check instance is authorized:
     `GET https://api.green-api.com/waInstance<ID>/getStateInstance/<TOKEN>` → `authorized`
4. Creds live in `backend/.env`: `GREENAPI_ID_INSTANCE`, `GREENAPI_API_TOKEN` (gitignored).

### Demo-safety note
If ngrok is flaky during the demo, the WhatsApp path can still be **shown via the loopback**
(curl POST to `localhost:8000/webhook/greenapi`) which sends a real WhatsApp reply — but for a
judge to message it from *their* phone, ngrok + webhook must be live. The **web demo does not
depend on ngrok** and is the safer primary.

---

## RUN COMMANDS (three terminals)

**Terminal 1 — Backend** (from `backend/` so data paths resolve):
```powershell
cd C:\Users\akuls\OneDrive\Documents\Projects\krishigpt\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Health: `curl http://localhost:8000/health` → `chunks_loaded: 45`.

**Terminal 2 — Frontend:**
```powershell
cd C:\Users\akuls\OneDrive\Documents\Projects\krishigpt\frontend
npm run dev      # http://localhost:3000
```

**Terminal 3 — ngrok (only if demoing WhatsApp):**
```powershell
ngrok http 8000
```

---

## DEMO SCRIPT (≈4 min)

**Opening (20s):** "Most Indian farmers can't get expert advice in their own language or for
their own region. KrishiGPT does both — grounded in official ICAR documents."

**Demo 1 — Web, English + region (60s):**
1. Open http://localhost:3000
2. PIN `560001` → badge: "Karnataka · Deccan-South"
3. Ask: "How do I control stem borer in paddy?"
4. Show the grounded answer + expand **Sources** (Karnataka docs).

**Demo 2 — The differentiator (45s):** *(the core research claim)*
1. Change PIN to `141001` (Punjab), ask "When should I apply urea to wheat?"
2. Show sources are now **Punjab** docs. "Same system, different region → different
   official source. That's region-aware retrieval."

**Demo 3 — Multilingual (45s):**
1. Switch language to हिन्दी or ಕನ್ನಡ, ask the same kind of question.
2. Answer comes back in that script. "7 Indic languages, same grounding."

**Demo 4 — WhatsApp (45s, if ngrok up):**
1. From a phone, message the bot (918160407939): the onboarding → language → pincode →
   question flow. "No app to download — farmers already have WhatsApp."

**Results slide (30s):** the ablation table:
> "On our evaluation set, region-aware retrieval puts the correct-state document at rank #1
> 100% of the time (vs 56% without), and drops hallucination from 20% to 0%."
Re-run live if you like: `python scripts/evaluate.py --no-generation` (zero quota).

**Close (15s):** "Grounded, regional, multilingual, on WhatsApp — auditable and open."

---

## Things to remember / gotchas for tomorrow
- **Gemini free tier = 20 requests/day per model.** It resets ~midnight Pacific. If it 429s
  mid-demo, the generator **auto-falls-over to Groq** — answers keep coming (slightly weaker
  Indic quality). Add more keys to `GOOGLE_API_KEYS` (comma-separated) for more headroom.
- **Restart the backend** after any `.env` change (keys, model) — env is read at startup.
- **Retrieval ablation needs no quota** (`--no-generation`) — safe to run live on stage.
- The **eval numbers are on a 45-chunk / 20-question demo set** — present as "on our
  evaluation set," not a production claim. Methodology (ablation, MRR, faithfulness) is sound.
- IDE shows red squiggles ("cannot find module") — false; it points at system Python, not
  `.venv`. Runtime is fine. Point the IDE interpreter at `.venv\Scripts\python.exe` to silence.
- `.env` (all keys) is gitignored — never commit it.

## Pending / optional (only if time)
- Voice notes (Bhashini ASR) — code exists in `integrations/bhashini.py`, untested, needs
  Bhashini keys. Skip unless you have spare time.
- Real ICAR PDF scraping to enlarge corpus — current corpus is curated seed docs.
