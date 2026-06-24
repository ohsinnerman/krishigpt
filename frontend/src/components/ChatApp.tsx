"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { sendChat, resolvePin } from "@/lib/api";
import { LANGUAGES, EXAMPLE_QUESTIONS, UI_TEXT } from "@/lib/constants";
import type { ChatMessage, RegionInfo } from "@/lib/types";

const CARD_COLORS = [
  { accent: "#4ade80", glow: "rgba(74,222,128,0.16)" },
  { accent: "#60a5fa", glow: "rgba(96,165,250,0.16)" },
  { accent: "#a78bfa", glow: "rgba(167,139,250,0.16)" },
  { accent: "#f472b6", glow: "rgba(244,114,182,0.16)" },
];

export default function ChatApp() {
  const [language, setLanguage] = useState("en");
  const [pincode, setPincode] = useState("");
  const [region, setRegion] = useState<RegionInfo | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const ui = UI_TEXT[language] ?? UI_TEXT.en;
  const examples = EXAMPLE_QUESTIONS[language] ?? EXAMPLE_QUESTIONS.en;
  const started = messages.length > 0;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const pin = pincode.trim();
    if (/^\d{6}$/.test(pin)) resolvePin(pin).then(setRegion);
    else setRegion(null);
  }, [pincode]);

  async function handleSend(text?: string) {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setError(null);
    setInput("");
    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), role: "user", content: message, language, timestamp: new Date() },
    ]);
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
    <div className="kg-shell">
      {/* ── Nav ── */}
      <nav className="kg-nav">
        <Link href="/" className="kg-brand">
          <div className="kg-logo">🌾</div>
          <div>
            <div className="kg-brand-name">KrishiGPT</div>
            <div className="kg-brand-tag">Your farming expert, in your language</div>
          </div>
        </Link>

        <div className="kg-controls">
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="kg-pill kg-select">
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code} style={{ color: "#000" }}>
                {l.native}
              </option>
            ))}
          </select>
          <input
            value={pincode}
            onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="PIN"
            inputMode="numeric"
            className="kg-pill kg-pin"
          />
          <div className="kg-pill kg-online">
            <span className="kg-dot" />
            <span>Online</span>
          </div>
        </div>
      </nav>

      {region && (
        <div className="kg-region">
          <span style={{ color: "var(--lime)" }}>📍</span>
          {region.district !== "Unknown" ? `${region.district}, ` : ""}
          {region.state} · {region.agro_zone}
        </div>
      )}

      {/* ── Body ── */}
      <main className="kg-main">
        {!started ? (
          <div className="kg-landing">
            <div>
              <span className="kg-hi">
                Hi, Farmer <span className="kg-wave">👋</span>
              </span>
              <h2 className="kg-greet">How may I help you today?</h2>
              <p className="kg-sub">
                Ask about your crop, pest, fertilizer or a government scheme. Set your PIN code
                above for region-specific advice.
              </p>
            </div>

            <div className="kg-cards">
              {examples.map((q, i) => {
                const c = CARD_COLORS[i % CARD_COLORS.length];
                return (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="kg-card"
                    style={{ borderColor: `${c.accent}33`, boxShadow: `0 14px 34px ${c.glow}` }}
                  >
                    <div className="kg-card-ico" style={{ background: c.glow }}>🌱</div>
                    <span className="kg-card-q">{q}</span>
                    <div className="kg-card-arrow" style={{ background: c.accent }}>↗</div>
                  </button>
                );
              })}
            </div>
            {error && <p className="kg-error">{error}</p>}
          </div>
        ) : (
          <div ref={scrollRef} className="kg-thread">
            {messages.map((m) => (
              <Bubble key={m.id} msg={m} />
            ))}
            {loading && (
              <div className="kg-typing">
                {[0, 1, 2].map((i) => (
                  <span key={i} className="kg-bdot" style={{ animationDelay: `${i * 0.2}s` }} />
                ))}
                <span style={{ marginLeft: 4 }}>{ui.thinking}</span>
              </div>
            )}
            {error && <p className="kg-error">{error}</p>}
          </div>
        )}

        {/* Input */}
        <div className="kg-input-wrap">
          <div className="kg-input-bar">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={ui.placeholder}
              className="kg-input"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="kg-send"
              aria-label="Send"
            >
              ↑
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

function Bubble({ msg }: { msg: ChatMessage }) {
  const [open, setOpen] = useState(false);
  const isUser = msg.role === "user";
  return (
    <div className={`kg-row ${isUser ? "kg-row-user" : ""}`}>
      <div className={isUser ? "kg-bubble kg-bubble-user" : "kg-bubble kg-bubble-bot"}>
        <p className="kg-bubble-text">{msg.content}</p>
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div className="kg-src">
            <button onClick={() => setOpen((s) => !s)} className="kg-src-toggle">
              {open ? "▾" : "▸"} Sources ({msg.sources.length})
              {msg.latency_ms != null && (
                <span className="kg-src-meta">{msg.cache_hit ? "⚡ cached" : `${msg.latency_ms}ms`}</span>
              )}
            </button>
            {open && (
              <div className="kg-src-list">
                {msg.sources.map((s, i) => (
                  <div key={i} className="kg-src-card">
                    <div className="kg-src-title">{s.title}</div>
                    <div className="kg-src-chips">
                      <span className="kg-chip" style={{ background: "rgba(74,222,128,0.16)", color: "#4ade80" }}>{s.state}</span>
                      <span className="kg-chip" style={{ background: "rgba(96,165,250,0.16)", color: "#60a5fa" }}>{s.topic}</span>
                      <span className="kg-chip" style={{ background: "rgba(255,255,255,0.06)", color: "rgba(242,242,240,0.5)" }}>score {s.score}</span>
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
