"use client";

import { useState, useRef, useEffect } from "react";
import { sendChat, resolvePin } from "@/lib/api";
import { LANGUAGES, EXAMPLE_QUESTIONS, UI_TEXT } from "@/lib/constants";
import type { ChatMessage, RegionInfo } from "@/lib/types";

export default function Home() {
  const [language, setLanguage] = useState("en");
  const [pincode, setPincode] = useState("");
  const [region, setRegion] = useState<RegionInfo | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const ui = UI_TEXT[language] ?? UI_TEXT.en;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const pin = pincode.trim();
    if (pin.length === 6 && /^\d{6}$/.test(pin)) {
      resolvePin(pin).then(setRegion);
    } else {
      setRegion(null);
    }
  }, [pincode]);

  async function handleSend(text?: string) {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setError(null);
    setInput("");

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
      language,
      timestamp: new Date(),
    };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    try {
      const res = await sendChat({ message, language, pincode: pincode || undefined });
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.response,
          sources: res.sources,
          region: res.region,
          language: res.language,
          latency_ms: res.latency_ms,
          cache_hit: res.cache_hit,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-green-50">
      {/* Header */}
      <header className="bg-green-700 text-white px-4 py-3 shadow-md">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">🌾 KrishiGPT</h1>
              <p className="text-green-100 text-xs">Your farming expert, in your language</p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-green-800 text-white text-sm rounded-md px-2 py-1.5 border border-green-600 focus:outline-none"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>{l.native}</option>
                ))}
              </select>
              <input
                value={pincode}
                onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="PIN code"
                inputMode="numeric"
                className="w-24 text-sm rounded-md px-2 py-1.5 text-gray-900 bg-white border border-green-600 focus:outline-none"
              />
            </div>
          </div>
          {region && (
            <div className="mt-2 inline-block bg-green-600 rounded-full px-3 py-0.5 text-xs">
              📍 {region.district !== "Unknown" ? `${region.district}, ` : ""}
              {region.state} · {region.agro_zone}
            </div>
          )}
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center mt-8">
              <p className="text-gray-500 mb-3">{ui.examples}</p>
              <div className="flex flex-col gap-2 max-w-md mx-auto">
                {(EXAMPLE_QUESTIONS[language] ?? EXAMPLE_QUESTIONS.en).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="text-left text-sm bg-white border border-green-200 rounded-lg px-4 py-2.5 hover:bg-green-100 transition text-gray-800 shadow-sm"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <ChatBubble key={m.id} msg={m} />
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-green-700">
              <span className="animate-pulse">🌾</span>
              <span className="text-sm">{ui.thinking}</span>
            </div>
          )}
          {error && <p className="text-red-600 text-sm">{error}</p>}
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-green-200 px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={ui.placeholder}
            className="flex-1 rounded-full border border-green-300 px-4 py-2.5 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="bg-green-700 text-white rounded-full px-6 py-2.5 font-medium disabled:opacity-50 hover:bg-green-800 transition"
          >
            {ui.send}
          </button>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ msg }: { msg: ChatMessage }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = msg.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 shadow-sm ${
          isUser ? "bg-green-700 text-white" : "bg-white text-gray-900 border border-green-100"
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-green-100">
            <button
              onClick={() => setShowSources((s) => !s)}
              className="text-xs text-green-700 font-medium"
            >
              {showSources ? "▼" : "▶"} Sources ({msg.sources.length})
              {msg.latency_ms != null && (
                <span className="text-gray-400 font-normal ml-2">
                  {msg.cache_hit ? "⚡ cached" : `${msg.latency_ms}ms`}
                </span>
              )}
            </button>
            {showSources && (
              <div className="mt-2 space-y-1.5">
                {msg.sources.map((s, i) => (
                  <div key={i} className="text-xs bg-green-50 rounded-md px-2.5 py-1.5">
                    <div className="font-medium text-gray-800">{s.title}</div>
                    <div className="text-gray-500 flex gap-2 mt-0.5 flex-wrap">
                      <span className="bg-green-200 rounded px-1.5">{s.state}</span>
                      <span className="bg-blue-100 rounded px-1.5">{s.topic}</span>
                      <span>score {s.score}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
