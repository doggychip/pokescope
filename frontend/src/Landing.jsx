import { useNavigate } from "react-router-dom";
import "./Landing.css";

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const isDevMode = !clerkKey || clerkKey === "pk_test_PLACEHOLDER";

const FEATURES = [
  {
    icon: "\ud83d\udcc8",
    title: "Real-Time Valuations",
    desc: "Fair value estimates powered by market data across eBay, Fanatics Collect, and PriceCharting.",
    free: true,
  },
  {
    icon: "\ud83d\udea8",
    title: "Bubble Risk Alerts",
    desc: "Proprietary scoring that flags overheated cards before the correction hits.",
    free: true,
  },
  {
    icon: "\ud83d\udd0d",
    title: "20,000+ Cards Tracked",
    desc: "Every English-language TCG set from Base Set to Scarlet & Violet, plus curated Japanese grails.",
    free: true,
  },
  {
    icon: "\ud83c\udfaf",
    title: "Scarcity Analysis",
    desc: "PSA population data cross-referenced with price trends to find undervalued gems.",
    free: false,
  },
  {
    icon: "\ud83e\udd16",
    title: "AI Card Analysis",
    desc: "One-click deep dives on any card: valuation context, momentum signals, and buy/sell guidance.",
    free: false,
  },
  {
    icon: "\ud83d\udcca",
    title: "Portfolio Tracker",
    desc: "Track your collection's value over time with automated price updates and P&L reporting.",
    free: false,
  },
];

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    cta: "Get Started Free",
    highlight: false,
    features: [
      "20,000+ card database",
      "Basic search & filters",
      "Market overview stats",
      "Top 200 cards by sort",
      "Community access",
    ],
    limits: [
      "No AI analysis",
      "No portfolio tracking",
      "No export",
    ],
  },
  {
    name: "Pro",
    price: "$12",
    period: "/month",
    cta: "Start 14-Day Free Trial",
    highlight: true,
    features: [
      "Everything in Free",
      "Unlimited card views",
      "AI analysis on every card",
      "Scarcity deep dives",
      "Portfolio tracker",
      "Price alerts & watchlists",
      "CSV/API export",
      "Priority support",
    ],
    limits: [],
  },
  {
    name: "Dealer",
    price: "$49",
    period: "/month",
    cta: "Contact Sales",
    highlight: false,
    features: [
      "Everything in Pro",
      "Bulk valuation tools",
      "Inventory management",
      "Market API access",
      "Custom reports",
      "Multi-user accounts",
      "Dedicated account manager",
      "White-label options",
    ],
    limits: [],
  },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <span className="nav-icon">&#9889;</span>
          <span className="nav-name">POK&Eacute;SCOPE</span>
        </div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <button className="nav-cta" onClick={() => navigate(isDevMode ? "/dashboard" : "/sign-in")}>Sign In</button>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">PTCG MARKET INTELLIGENCE</div>
        <h1>
          Stop guessing.<br />
          <span className="hero-accent">Start knowing.</span>
        </h1>
        <p className="hero-sub">
          Real-time valuations, bubble risk alerts, and AI-powered analysis for 20,000+ Pok&eacute;mon cards.
          Make smarter collecting and investing decisions.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={() => navigate(isDevMode ? "/dashboard" : "/sign-up")}>
            Get Started Free
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById("features").scrollIntoView({ behavior: "smooth" })}>
            See How It Works
          </button>
        </div>
        <p className="hero-note">No credit card required &middot; Free forever &middot; 20,000+ cards</p>
      </section>

      {/* Stats strip */}
      <section className="stats-strip">
        {[
          { value: "20,245", label: "Cards Tracked" },
          { value: "500+", label: "Sets Covered" },
          { value: "Real-Time", label: "Price Updates" },
          { value: "97.5%", label: "Market Coverage" },
        ].map((s, i) => (
          <div key={i} className="stats-strip-item">
            <div className="stats-strip-value">{s.value}</div>
            <div className="stats-strip-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Screenshot preview */}
      <section className="preview">
        <div className="preview-window">
          <div className="preview-bar">
            <div className="preview-dots">
              <span /><span /><span />
            </div>
            <div className="preview-url">localhost:3000/dashboard</div>
          </div>
          <div className="preview-body">
            <div className="preview-table">
              <div className="preview-row preview-header-row">
                {["Card", "Price", "Fair Value", "Signal", "Bubble"].map(h => (
                  <div key={h} className="preview-cell">{h}</div>
                ))}
              </div>
              {[
                { name: "Charizard Gold Star \u03b4", price: "$10,500", fair: "$11,000", signal: "FAIR", signalColor: "#f59e0b", bubble: "LOW", bubbleIcon: "\ud83d\udfe2" },
                { name: "Crystal Lugia", price: "$8,000", fair: "$10,500", signal: "UNDERVALUED", signalColor: "#22c55e", bubble: "LOW", bubbleIcon: "\ud83d\udfe2" },
                { name: "Luigi Pikachu Full Art", price: "$17,000", fair: "$12,000", signal: "OVERVALUED", signalColor: "#ef4444", bubble: "HIGH", bubbleIcon: "\ud83d\udd34" },
                { name: "Umbreon VMAX Alt Art", price: "$3,500", fair: "$4,200", signal: "UNDERVALUED", signalColor: "#22c55e", bubble: "LOW", bubbleIcon: "\ud83d\udfe2" },
              ].map((r, i) => (
                <div key={i} className="preview-row">
                  <div className="preview-cell preview-name">{r.name}</div>
                  <div className="preview-cell">{r.price}</div>
                  <div className="preview-cell" style={{ color: "#9ca3af" }}>{r.fair}</div>
                  <div className="preview-cell"><span className="preview-badge" style={{ color: r.signalColor, borderColor: `${r.signalColor}40` }}>{r.signal}</span></div>
                  <div className="preview-cell">{r.bubbleIcon} {r.bubble}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features" id="features">
        <h2>Everything you need to collect smarter</h2>
        <p className="section-sub">From casual collectors to full-time dealers, PokéScope gives you the edge.</p>
        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
              <span className={`feature-tier ${f.free ? "tier-free" : "tier-pro"}`}>
                {f.free ? "Free" : "Pro"}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="pricing" id="pricing">
        <h2>Simple, transparent pricing</h2>
        <p className="section-sub">Start free. Upgrade when you need more.</p>
        <div className="pricing-grid">
          {TIERS.map((tier, i) => (
            <div key={i} className={`pricing-card ${tier.highlight ? "pricing-highlight" : ""}`}>
              {tier.highlight && <div className="pricing-popular">MOST POPULAR</div>}
              <h3>{tier.name}</h3>
              <div className="pricing-price">
                <span className="pricing-amount">{tier.price}</span>
                <span className="pricing-period">{tier.period}</span>
              </div>
              <button
                className={tier.highlight ? "btn-primary" : "btn-secondary"}
                onClick={() => navigate(isDevMode ? "/dashboard" : "/sign-up")}
              >
                {tier.cta}
              </button>
              <ul className="pricing-features">
                {tier.features.map((f, j) => (
                  <li key={j} className="pricing-yes">{f}</li>
                ))}
                {tier.limits.map((f, j) => (
                  <li key={`n${j}`} className="pricing-no">{f}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="final-cta">
        <h2>Ready to see what your cards are really worth?</h2>
        <p>Join thousands of collectors using PokéScope to make smarter decisions.</p>
        <button className="btn-primary btn-lg" onClick={() => navigate(isDevMode ? "/dashboard" : "/sign-up")}>
          Get Started Free
        </button>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-brand">
          <span>&#9889;</span> POK&Eacute;SCOPE
        </div>
        <p>&copy; 2026 PokéScope. Not financial advice. Built for collectors, by collectors.</p>
      </footer>
    </div>
  );
}
