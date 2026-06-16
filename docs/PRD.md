# KrishiGPT — Product Requirements Document

**Version:** 1.0  
**Status:** Active  
**Last Updated:** June 2026  

---

## 1. Problem Statement

Indian agriculture employs 600M+ people. Farmers routinely make high-stakes decisions — which crop variety to plant, when to irrigate, how to treat a pest — with no access to expert guidance. Extension officers (one per ~800 farmers) cannot cover demand. Existing digital tools fail because:

1. They are in English only
2. They give generic national-level advice, not state/zone-specific guidance
3. They require literacy (text-only interfaces)
4. They are closed-source and cannot be audited for accuracy

The result: farmers rely on pesticide dealers who have a financial incentive to oversell. A recent NITI Aayog study (2024) found that 43% of pesticide use in India is unnecessary and driven by information asymmetry.

---

## 2. Target Users

### Primary: Small and Marginal Farmers
- Land holding: < 2 hectares
- Literacy: Variable; many are functionally illiterate in English
- Language: Native speaker of one of 22 scheduled languages
- Device: Android smartphone (entry-level), WhatsApp installed
- Connectivity: 2G/3G, sometimes 4G
- Pain point: "I don't know if this advice is right for my soil / my district / this season"

### Secondary: Agricultural Extension Officers (KVK staff)
- Use the system to prep for farmer visits
- Need to pull scheme documents quickly
- Fluent in English + regional language

### Tertiary: Researchers / Developers
- Open-source contributors
- Academics building on the corpus and evaluation set

---

## 3. Core Features

### 3.1 Regional Question Answering (P0 — Must Have)
- Farmer types or speaks a question
- System detects or accepts their pin code
- Retriever filters FAISS index by state + agro-climatic zone
- LLM synthesizes answer in farmer's language
- Response includes source document names and states
- Max response latency: 8 seconds (P99)

### 3.2 Multilingual Support (P0 — Must Have)
- Input: English, Hindi, Kannada, Tamil, Telugu, Marathi, Gujarati, Punjabi
- Output: Same language as input (auto-detected)
- Language selector in UI for explicit override
- Translation pipeline: Bhashini IndicTrans2

### 3.3 Voice Interface (P0 — Must Have for WhatsApp, P1 for Web)
- Farmer sends voice note on WhatsApp
- Bhashini ASR transcribes audio → text
- System answers in text + optionally synthesizes audio response (TTS)
- Web: microphone button triggers browser speech recognition with Bhashini fallback

### 3.4 Government Scheme Guidance (P1 — Should Have)
- PMFBY (crop insurance): eligibility, enrollment dates, claim process
- PMKISAN: registration, beneficiary status check, installment schedule
- KCC (Kisan Credit Card): eligibility, application process, documents needed
- Answers must be state-specific (different nodal banks, different cutoff dates)

### 3.5 Source Attribution (P1 — Should Have)
- Every response shows which documents were retrieved
- Shows state and agro-climatic zone of each source
- Farmer can see "This answer is based on ICAR Package of Practices for Karnataka"

### 3.6 Feedback Loop (P1 — Should Have)
- Simple 👍/👎 reaction on each answer
- Negative feedback triggers a flagging queue for human review
- Feedback stored per language, per region, per query type

### 3.7 Multi-modal Plant Diagnosis (P2 — Nice to Have)
- Farmer uploads photo of diseased leaf or crop
- Vision model (Gemini Pro Vision) classifies disease
- RAG retrieves treatment protocol for that disease + that state
- Response: diagnosis + treatment + preventive measures

### 3.8 WhatsApp Channel (P0 — Must Have)
- Twilio WhatsApp Business API webhook
- Stateful sessions (remember language + pincode per phone number)
- Rate limiting: 10 messages/hour per number (free tier)
- Handles voice notes, text, and images

---

## 4. Non-Functional Requirements

### Performance
| Metric | Target |
|---|---|
| P50 response latency | < 4 seconds |
| P99 response latency | < 8 seconds |
| FAISS search latency | < 200ms |
| Embedding inference | < 500ms |
| Gemini API latency | < 3 seconds |
| Concurrent users | 50 (MVP), 500 (v1) |

### Accuracy
| Metric | Target |
|---|---|
| Hallucination rate | < 15% (vs 25–35% without region-grounding) |
| Answer relevance (human eval) | > 75% |
| Source attribution accuracy | > 90% |
| Language detection accuracy | > 98% |

### Reliability
- Uptime: 99% (acceptable for MVP)
- Graceful degradation: if Gemini is down, respond with retrieved text only
- If Bhashini is down, skip translation (return in English)

### Security
- No PII stored beyond phone number hash + session data
- Session data auto-deleted after 30 days
- API keys in environment variables only, never committed
- Twilio webhook signature validation

### Accessibility
- WCAG 2.1 AA for web interface
- Voice-first design for low-literacy users
- Font size minimum 16px
- High-contrast mode

---

## 5. Out of Scope (v1)

- Real-time weather integration
- Market price data
- Soil test integration
- Crop planning calendar
- Farmer profile / personalization
- Bengali, Odia, Malayalam (v2)
- iOS app (WhatsApp + web covers the use case)
- Multi-turn memory beyond session

---

## 6. Success Metrics

### Launch Criteria (Day 0)
- [ ] System answers questions correctly in all 7 languages
- [ ] Region filtering works for all 28 states + 8 UTs
- [ ] WhatsApp webhook handles voice + text
- [ ] Response latency < 8s P99
- [ ] Zero PII in logs

### 30-Day Metrics
- 100 unique conversations
- Average session length: 3+ messages
- Positive feedback rate: > 60%
- Zero hallucinations on scheme documents (zero tolerance for wrong eligibility info)

### Academic Metrics
- Hallucination rate reduction vs non-region-aware baseline: > 10%
- Evaluation on 500 KCC transcript queries
- BLEU/chrF scores for multilingual output

---

## 7. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gemini API rate limits | High | High | Redis cache; Llama-3-8B fallback |
| Bhashini downtime | Medium | High | Skip TTS, return text; browser STT fallback |
| ICAR PDFs have poor OCR | High | Medium | PyMuPDF + Tesseract fallback; manual spot-check |
| Wrong scheme information | Low | Very High | Zero-retrieval guard: if no doc found, say "I don't know" |
| FAISS index too large | Low | Medium | Chunk limit 512 tokens; quantize with IVFFlat if > 100k chunks |
| Twilio cost overrun | Medium | Low | Rate limiting per number; billing alerts |

---

## 8. Definition of Done

A feature is done when:
1. Unit tests pass (>80% coverage)
2. Manual test with real farmer question in each language passes
3. Response time is within SLA
4. No hardcoded credentials
5. Documented in API.md
