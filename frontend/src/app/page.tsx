import Link from "next/link";

const WHATSAPP_NUMBER = "918160407939";
const WHATSAPP_LINK = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent("Hi KrishiGPT")}`;

export default function Landing() {
  return (
    <div className="lp">
      <nav className="kg-nav">
        <div className="kg-brand">
          <div className="kg-logo">🌾</div>
          <div>
            <div className="kg-brand-name">KrishiGPT</div>
            <div className="kg-brand-tag">Your farming expert, in your language</div>
          </div>
        </div>
        <div className="kg-controls">
          <Link href="/chat" className="kg-pill" style={{ textDecoration: "none" }}>
            Open chat →
          </Link>
        </div>
      </nav>

      <section className="lp-hero">
        <span className="lp-badge">🌱 Region-aware · Multilingual · Grounded in ICAR</span>
        <h1 className="lp-title">Farming advice,<br />in your language.</h1>
        <p className="lp-tag">
          KrishiGPT answers questions about crops, pests, fertilizers and government schemes —
          tailored to your region and grounded in official ICAR Package of Practices. Available in
          7 Indian languages, on the web and on WhatsApp.
        </p>

        <div className="lp-cta">
          <Link href="/chat" className="lp-btn lp-btn-primary">
            💬 Chat here on the website
          </Link>
          <a href={WHATSAPP_LINK} target="_blank" rel="noopener noreferrer" className="lp-btn lp-btn-wa">
            <span style={{ fontSize: 18 }}>🟢</span> Chat on WhatsApp
          </a>
        </div>
        <p style={{ fontSize: 12.5, color: "rgba(242,242,240,0.4)", margin: 0 }}>
          WhatsApp: +91 81604 07939 — send “Hi” to begin
        </p>

        <div className="lp-features">
          <div className="lp-feat">
            <div style={{ fontSize: 20 }}>📍</div>
            <h3 className="lp-feat-h">Region-aware</h3>
            <p className="lp-feat-p">Enter your PIN code and get advice matched to your state and agro-climatic zone.</p>
          </div>
          <div className="lp-feat">
            <div style={{ fontSize: 20 }}>🗣️</div>
            <h3 className="lp-feat-h">7 languages</h3>
            <p className="lp-feat-p">English, Hindi, Kannada, Tamil, Telugu, Marathi, Gujarati and Punjabi.</p>
          </div>
          <div className="lp-feat">
            <div style={{ fontSize: 20 }}>📄</div>
            <h3 className="lp-feat-h">Grounded answers</h3>
            <p className="lp-feat-p">Every reply cites the official source document, so advice is auditable — not invented.</p>
          </div>
        </div>
      </section>

      <footer className="lp-foot">KrishiGPT · region-aware multilingual RAG agricultural advisor</footer>
    </div>
  );
}
