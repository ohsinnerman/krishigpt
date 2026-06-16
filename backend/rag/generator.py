import os
from typing import Optional

from google import genai
from google.genai import types as genai_types

_GENAI_READY = False
_clients: list = []      # one client per API key
_active = 0              # index of the key currently in use


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _collect_keys() -> list[str]:
    """Keys from GOOGLE_API_KEYS (comma-separated) plus single GOOGLE_API_KEY,
    de-duplicated, order preserved."""
    raw = []
    raw += [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",")]
    raw.append(os.getenv("GOOGLE_API_KEY", "").strip())
    seen, keys = set(), []
    for k in raw:
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


def _ensure_clients() -> list:
    """Lazily build one Gemini client per key. Empty list if no keys."""
    global _GENAI_READY, _clients
    if _GENAI_READY:
        return _clients
    keys = _collect_keys()
    if not keys:
        print("WARNING: no Gemini key set (GOOGLE_API_KEY / GOOGLE_API_KEYS). Generator stubs.")
    else:
        _clients = [genai.Client(api_key=k) for k in keys]
        print(f"Gemini ready with {len(_clients)} API key(s); auto-rotates on quota/429.")
    _GENAI_READY = True
    return _clients


def _is_quota_error(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()


# ── Groq fallback (used only when all Gemini keys are exhausted) ──────────────
_GROQ_READY = False
_groq_client = None


def _groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _ensure_groq():
    """Lazily build a Groq client. Returns it or None if no GROQ_API_KEY."""
    global _GROQ_READY, _groq_client
    if _GROQ_READY:
        return _groq_client
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=key)
            print(f"Groq fallback ready ({_groq_model()}).")
        except Exception as e:
            print(f"WARNING: Groq init failed: {e}")
            _groq_client = None
    _GROQ_READY = True
    return _groq_client


def _groq_call(prompt: str, max_tokens: int) -> Optional[str]:
    client = _ensure_groq()
    if client is None:
        return None
    resp = client.chat.completions.create(
        model=_groq_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        top_p=0.8,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
}

# Language-specific instruction (in the target language — forces correct output)
LANGUAGE_INSTRUCTIONS = {
    "en": "Respond in clear, simple English that a farmer can understand.",
    "hi": "केवल हिन्दी में जवाब दें। सरल शब्दों में लिखें जो एक किसान समझ सके। अंग्रेजी के शब्द कम से कम प्रयोग करें।",
    "kn": "ಕೇವಲ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ. ರೈತರಿಗೆ ಅರ್ಥವಾಗುವ ಸರಳ ಭಾಷೆ ಬಳಸಿ. ಇಂಗ್ಲಿಷ್ ಪದಗಳನ್ನು ತಪ್ಪಿಸಿ.",
    "ta": "தமிழிலே மட்டும் பதில் சொல்லுங்கள். விவசாயிகளுக்கு புரியும் எளிய வார்த்தைகளை பயன்படுத்துங்கள்.",
    "te": "తెలుగులో మాత్రమే సమాధానం ఇవ్వండి. రైతులకు అర్థమయ్యే సాధారణ పదాలు వాడండి.",
    "mr": "केवळ मराठीत उत्तर द्या. शेतकऱ्यांना समजेल अशा सोप्या भाषेत लिहा.",
    "gu": "ફક્ત ગુજરાતીમાં જ જવાબ આપો. ખેડૂતોને સમજાય તેવી સરળ ભાષા વાપરો.",
    "pa": "ਸਿਰਫ਼ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। ਕਿਸਾਨਾਂ ਨੂੰ ਸਮਝ ਆਉਣ ਵਾਲੀ ਸਰਲ ਭਾਸ਼ਾ ਵਰਤੋ।",
}

# Terms that must NEVER be translated
PRESERVE_TERMS = "NPK, DAP, Urea, PMFBY, PMKISAN, KCC, pH, MSP, KVK, ICAR"


def build_prompt(
    question: str,
    context_chunks: list[dict],
    language: str,
    region: Optional[str],
) -> str:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    region_context = f"The farmer is from {region}." if region else "The farmer's region is not specified."

    if context_chunks:
        context_sections = []
        for i, chunk in enumerate(context_chunks, 1):
            context_sections.append(
                f"[Document {i}: {chunk.get('source_title', 'Unknown')}, "
                f"State: {chunk.get('state', 'pan-india')}]\n"
                f"{chunk['text']}"
            )
        context = "\n\n".join(context_sections)
    else:
        context = "No specific documents found in the knowledge base."

    prompt = f"""You are KrishiGPT, a trusted agricultural advisor for Indian farmers. Your knowledge base is built from official ICAR (Indian Council of Agricultural Research) Package of Practices and Government of India scheme guidelines. You answer using ONLY the official documents provided below.

REGIONAL CONTEXT: {region_context}

CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
These technical terms must NEVER be translated, always keep as-is: {PRESERVE_TERMS}

OFFICIAL SOURCE DOCUMENTS (your only source of facts):
{context}

FARMER'S QUESTION: {question}

RESPONSE RULES:
1. Answer ONLY in {lang_name}. Not a single sentence in any other language.
2. ANSWER FROM THE DOCUMENTS ABOVE. The documents above ARE your knowledge base — if the answer is present in them (even partially), give a confident, complete answer using those facts. Do NOT refuse or deflect when the information is available above.
3. Ground every fact in the documents. Use the specific varieties, dosages, timings, and figures stated in the documents — quote the numbers verbatim. NEVER invent numbers, dosages, dates, or eligibility rules that are not in the documents above.
4. Attribute naturally so the advice sounds official, e.g. "As per the ICAR Package of Practices for {region or 'your region'}..." or "According to the official guidelines...". Do not fabricate document names beyond what is provided.
5. For pest/disease questions: name the problem, give the specific treatment with dosage from the documents, and one prevention tip.
6. For fertilizer questions: give the specific dose (kg/hectare or kg/acre), timing, and method of application from the documents.
7. For scheme questions (PMFBY/PMKISAN/KCC): state eligibility, documents needed, and where to apply, exactly as in the documents.
8. ONLY IF the documents above genuinely do NOT contain anything relevant to the question: briefly say the official documents do not cover this specific point, and suggest contacting the local KVK. Use this fallback RARELY — never when an answer can be drawn from the documents above.
9. Keep the response to 4-6 sentences. Farmers need brevity.

RESPONSE IN {lang_name.upper()}:"""

    return prompt


def _build_config(max_tokens: int) -> genai_types.GenerateContentConfig:
    cfg = dict(max_output_tokens=max_tokens, temperature=0.3, top_p=0.8)
    # On Gemini 2.5 Flash, "thinking" tokens are billed against the output budget
    # and can swallow the whole answer. Disable thinking for fast factual replies.
    # (Field is ignored by models that don't support it.)
    try:
        cfg["thinking_config"] = genai_types.ThinkingConfig(thinking_budget=0)
    except Exception:
        pass
    return genai_types.GenerateContentConfig(**cfg)


def _call(prompt: str, max_tokens: int) -> str:
    """Generate with provider failover:
      1. Try each Gemini key (rotate on quota/429).
      2. If ALL Gemini keys are quota-exhausted, fall over to Groq.
    """
    global _active
    clients = _ensure_clients()
    quota_hit = False
    last_err = None

    for attempt in range(len(clients)):
        idx = (_active + attempt) % len(clients)
        try:
            response = clients[idx].models.generate_content(
                model=_model_name(),
                contents=prompt,
                config=_build_config(max_tokens),
            )
            _active = idx  # stick with the key that worked
            return (response.text or "").strip()
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                quota_hit = True
                print(f"  Gemini key #{idx + 1} hit quota; rotating...")
                continue
            raise

    # All Gemini keys failed. If it was a quota problem, try Groq.
    if quota_hit or not clients:
        groq_text = _groq_call(prompt, max_tokens)
        if groq_text is not None:
            print("  -> fell over to Groq.")
            return groq_text

    if last_err:
        raise last_err
    raise RuntimeError("No generation backend available.")


async def generate(
    question: str,
    context_chunks: list[dict],
    language: str,
    region: Optional[str],
    max_tokens: int = 500,
) -> str:
    """Generate via Gemini (primary) with Groq fallback. Degrades to a stub if
    neither provider has a key set."""
    clients = _ensure_clients()
    has_groq = _ensure_groq() is not None
    prompt = build_prompt(question, context_chunks, language, region)

    if not clients and not has_groq:
        # Stub: return retrieved context so the rest of the system is testable
        if context_chunks:
            snippet = context_chunks[0]["text"][:300]
            return f"[Demo mode — no Gemini/Groq key set]\nBased on retrieved docs: {snippet}"
        return "[Demo mode — no Gemini/Groq key set and no documents retrieved.]"

    text = _call(prompt, max_tokens)

    # Script validation — retry once with stronger instruction if wrong script
    if language != "en" and text and not _has_correct_script(text, language):
        stronger = f"IMPORTANT: Your ENTIRE response must be in {LANGUAGE_NAMES[language]} script only.\n\n" + prompt
        text = _call(stronger, max_tokens)

    return text


def _has_correct_script(text: str, lang: str) -> bool:
    """Check if text contains expected Unicode script characters."""
    SCRIPT_RANGES = {
        "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
        "kn": (0x0C80, 0x0CFF), "ta": (0x0B80, 0x0BFF),
        "te": (0x0C00, 0x0C7F), "gu": (0x0A80, 0x0AFF),
        "pa": (0x0A00, 0x0A7F),
    }
    if lang not in SCRIPT_RANGES:
        return True
    lo, hi = SCRIPT_RANGES[lang]
    script_chars = sum(1 for c in text if lo <= ord(c) <= hi)
    alpha_chars = sum(1 for c in text if c.isalpha())
    return alpha_chars > 0 and (script_chars / alpha_chars) > 0.25
