import type { Language } from "./types";

export const LANGUAGES: Language[] = [
  { code: "en", name: "English", native: "English" },
  { code: "hi", name: "Hindi", native: "हिन्दी" },
  { code: "kn", name: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ta", name: "Tamil", native: "தமிழ்" },
  { code: "te", name: "Telugu", native: "తెలుగు" },
  { code: "mr", name: "Marathi", native: "मराठी" },
  { code: "gu", name: "Gujarati", native: "ગુજરાતી" },
  { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ" },
];

export const EXAMPLE_QUESTIONS: Record<string, string[]> = {
  en: [
    "How do I control stem borer in paddy?",
    "What is the urea dose for wheat per acre?",
    "How do I apply for PMFBY crop insurance?",
  ],
  hi: [
    "धान में तना छेदक कीट कैसे नियंत्रित करें?",
    "गेहूं में प्रति एकड़ यूरिया की मात्रा क्या है?",
    "PMFBY फसल बीमा के लिए कैसे आवेदन करें?",
  ],
  kn: [
    "ಭತ್ತದಲ್ಲಿ ಕಾಂಡ ಕೊರೆಯುವ ಹುಳ ಹೇಗೆ ನಿಯಂತ್ರಿಸುವುದು?",
    "ಗೋಧಿಗೆ ಪ್ರತಿ ಎಕರೆ ಯೂರಿಯಾ ಪ್ರಮಾಣ ಎಷ್ಟು?",
    "PMFBY ಬೆಳೆ ವಿಮೆಗೆ ಹೇಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು?",
  ],
  ta: [
    "நெல்லில் தண்டு துளைப்பானை எப்படி கட்டுப்படுத்துவது?",
    "கோதுமைக்கு ஒரு ஏக்கருக்கு யூரியா அளவு என்ன?",
    "PMFBY பயிர் காப்பீட்டிற்கு எப்படி விண்ணப்பிப்பது?",
  ],
  te: [
    "వరిలో కాండం తొలిచే పురుగును ఎలా నియంత్రించాలి?",
    "గోధుమకు ఎకరానికి యూరియా మోతాదు ఎంత?",
    "PMFBY పంట బీమాకు ఎలా దరఖాస్తు చేయాలి?",
  ],
  mr: [
    "भातामध्ये खोड किडीचे नियंत्रण कसे करावे?",
    "गव्हासाठी प्रति एकर युरियाचे प्रमाण किती?",
    "PMFBY पीक विम्यासाठी अर्ज कसा करावा?",
  ],
  gu: [
    "ડાંગરમાં થડ કોરનાર જીવાતને કેવી રીતે નિયંત્રિત કરવી?",
    "ઘઉં માટે એકર દીઠ યુરિયાનું પ્રમાણ કેટલું?",
    "PMFBY પાક વીમા માટે કેવી રીતે અરજી કરવી?",
  ],
  pa: [
    "ਝੋਨੇ ਵਿੱਚ ਤਣਾ ਛੇਦਕ ਕੀੜੇ ਨੂੰ ਕਿਵੇਂ ਕੰਟਰੋਲ ਕਰੀਏ?",
    "ਕਣਕ ਲਈ ਪ੍ਰਤੀ ਏਕੜ ਯੂਰੀਆ ਦੀ ਮਾਤਰਾ ਕਿੰਨੀ ਹੈ?",
    "PMFBY ਫਸਲ ਬੀਮੇ ਲਈ ਕਿਵੇਂ ਅਰਜ਼ੀ ਦੇਈਏ?",
  ],
};

export const UI_TEXT: Record<string, { placeholder: string; thinking: string; examples: string; send: string }> = {
  en: { placeholder: "Ask about your crop, pest, fertilizer, or a scheme...", thinking: "Thinking...", examples: "Try asking:", send: "Send" },
  hi: { placeholder: "अपनी फसल, कीट, खाद या योजना के बारे में पूछें...", thinking: "सोच रहा हूँ...", examples: "ऐसे पूछें:", send: "भेजें" },
  kn: { placeholder: "ನಿಮ್ಮ ಬೆಳೆ, ಕೀಟ, ಗೊಬ್ಬರ ಬಗ್ಗೆ ಕೇಳಿ...", thinking: "ಯೋಚಿಸುತ್ತಿದೆ...", examples: "ಹೀಗೆ ಕೇಳಿ:", send: "ಕಳಿಸಿ" },
  ta: { placeholder: "உங்கள் பயிர், பூச்சி, உரம் பற்றி கேளுங்கள்...", thinking: "யோசிக்கிறேன்...", examples: "இப்படி கேளுங்கள்:", send: "அனுப்பு" },
  te: { placeholder: "మీ పంట, పురుగు, ఎరువు గురించి అడగండి...", thinking: "ఆలోచిస్తోంది...", examples: "ఇలా అడగండి:", send: "పంపు" },
  mr: { placeholder: "तुमच्या पिक, कीड, खत बद्दल विचारा...", thinking: "विचार करत आहे...", examples: "असे विचारा:", send: "पाठवा" },
  gu: { placeholder: "તમારા પાક, જીવાત, ખાતર વિશે પૂછો...", thinking: "વિચારી રહ્યું છે...", examples: "આમ પૂછો:", send: "મોકલો" },
  pa: { placeholder: "ਆਪਣੀ ਫਸਲ, ਕੀੜੇ, ਖਾਦ ਬਾਰੇ ਪੁੱਛੋ...", thinking: "ਸੋਚ ਰਿਹਾ ਹਾਂ...", examples: "ਇਸ ਤਰ੍ਹਾਂ ਪੁੱਛੋ:", send: "ਭੇਜੋ" },
};
