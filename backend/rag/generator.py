import os
from typing import Optional

from google import genai
from google.genai import types as genai_types

_GENAI_READY = False
_client = None


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _ensure_client():
    """Lazily build the Gemini client. Returns the client or None if no API key."""
    global _GENAI_READY, _client
    if _GENAI_READY:
        return _client
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not set. Generator will return a stub response.")
        _GENAI_READY = True
        _client = None
        return None
    _client = genai.Client(api_key=api_key)
    _GENAI_READY = True
    return _client


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

    prompt = f"""You are KrishiGPT, a trusted agricultural advisor for Indian farmers. You give practical, accurate advice based on official ICAR (Indian Council of Agricultural Research) documents.

REGIONAL CONTEXT: {region_context}

CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
These technical terms must NEVER be translated, always keep as-is: {PRESERVE_TERMS}

RETRIEVED AGRICULTURAL DOCUMENTS:
{context}

FARMER'S QUESTION: {question}

RESPONSE RULES:
1. Answer ONLY in {lang_name}. Not a single sentence in any other language.
2. Be practical and specific. A farmer should be able to act on your answer immediately.
3. For pest/disease questions: (a) Name what it is, (b) Give specific treatment with dosage from the documents, (c) Give one prevention tip.
4. For fertilizer questions: Give specific dose (kg/hectare or kg/acre), timing, and method of application.
5. For scheme questions (PMFBY/PMKISAN/KCC): State eligibility criteria, documents needed, and where to apply. Be PRECISE about dates and amounts — only state what is in the documents.
6. NEVER make up numbers, dosages, dates, or eligibility rules that are not in the retrieved documents.
7. If the documents don't contain the answer: Say you do not have exact information (in {lang_name}), then suggest contacting the local KVK.
8. End every response with ONE practical tip specific to {region or "the farmer's region"}.
9. Keep response to 4-6 sentences maximum. Farmers need brevity.

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


def _call(client, prompt: str, max_tokens: int) -> str:
    response = client.models.generate_content(
        model=_model_name(),
        contents=prompt,
        config=_build_config(max_tokens),
    )
    return (response.text or "").strip()


async def generate(
    question: str,
    context_chunks: list[dict],
    language: str,
    region: Optional[str],
    max_tokens: int = 500,
) -> str:
    """Generate response using Gemini. Degrades gracefully if no API key."""
    client = _ensure_client()
    prompt = build_prompt(question, context_chunks, language, region)

    if client is None:
        # Stub: return retrieved context so the rest of the system is testable
        if context_chunks:
            snippet = context_chunks[0]["text"][:300]
            return f"[Demo mode — no GOOGLE_API_KEY set]\nBased on retrieved docs: {snippet}"
        return "[Demo mode — no GOOGLE_API_KEY set and no documents retrieved.]"

    text = _call(client, prompt, max_tokens)

    # Script validation — retry once with stronger instruction if wrong script
    if language != "en" and text and not _has_correct_script(text, language):
        stronger = f"IMPORTANT: Your ENTIRE response must be in {LANGUAGE_NAMES[language]} script only.\n\n" + prompt
        text = _call(client, stronger, max_tokens)

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
