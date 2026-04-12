import { useNavigate } from "react-router-dom";
import { useTranslation, LANGS, langPrefix } from "./i18n/index.jsx";
import "./Landing.css";

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const isDevMode = !clerkKey || clerkKey === "pk_test_PLACEHOLDER";

const FEATURE_KEYS = [
  { icon: "\ud83d\udcc8", titleKey: "realTimeValuations", descKey: "realTimeValuationsDesc", free: true },
  { icon: "\ud83d\udea8", titleKey: "bubbleRiskAlerts", descKey: "bubbleRiskAlertsDesc", free: true },
  { icon: "\ud83d\udd0d", titleKey: "cardsTracked", descKey: "cardsTrackedDesc", free: true },
  { icon: "\ud83c\udfaf", titleKey: "scarcityAnalysis", descKey: "scarcityAnalysisDesc", free: false },
  { icon: "\ud83e\udd16", titleKey: "aiAnalysis", descKey: "aiAnalysisDesc", free: false },
  { icon: "\ud83d\udcca", titleKey: "portfolioTracker", descKey: "portfolioTrackerDesc", free: false },
];

function LangSwitcher() {
  const navigate = useNavigate();
  const { lang } = useTranslation();

  return (
    <div className="lang-switcher">
      {LANGS.map(l => (
        <button
          key={l.code}
          className={`lang-btn ${lang === l.code ? "active" : ""}`}
          onClick={() => navigate(l.code === "en" ? "/" : `/${l.code}`)}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { t, lang } = useTranslation();
  const prefix = langPrefix(lang);
  const dashPath = `${prefix}/dashboard`;
  const signInPath = isDevMode ? dashPath : "/sign-in";
  const signUpPath = isDevMode ? dashPath : "/sign-up";

  const tiers = [
    {
      name: t("pricing.free"), price: "$0", period: t("pricing.forever"),
      cta: t("pricing.getStartedFree"), highlight: false, tier: null,
      features: t("pricing.freeFeatures"), limits: t("pricing.freeLimits"),
    },
    {
      name: t("pricing.proName"), price: "$12", period: t("pricing.perMonth"),
      cta: t("pricing.startTrial"), highlight: true, tier: "pro",
      features: t("pricing.proFeatures"), limits: [],
    },
    {
      name: t("pricing.dealer"), price: "$49", period: t("pricing.perMonth"),
      cta: t("pricing.contactSales"), highlight: false, tier: "dealer",
      features: t("pricing.dealerFeatures"), limits: [],
    },
  ];

  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <span className="nav-icon">&#9889;</span>
          <span className="nav-name">POK&Eacute;SCOPE</span>
        </div>
        <div className="nav-links">
          <a href="#features">{t("nav.features")}</a>
          <a href="#pricing">{t("nav.pricing")}</a>
          <LangSwitcher />
          <button className="nav-cta" onClick={() => navigate(signInPath)}>{t("nav.signIn")}</button>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">{t("hero.badge")}</div>
        <h1>
          {t("hero.title1")}<br />
          <span className="hero-accent">{t("hero.title2")}</span>
        </h1>
        <p className="hero-sub">{t("hero.subtitle")}</p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={() => navigate(signUpPath)}>
            {t("hero.cta")}
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById("features").scrollIntoView({ behavior: "smooth" })}>
            {t("hero.ctaSecondary")}
          </button>
        </div>
        <p className="hero-note">{t("hero.note")}</p>
      </section>

      {/* Stats strip */}
      <section className="stats-strip">
        {[
          { value: "20,245", label: t("stats.cardsTracked") },
          { value: "500+", label: t("stats.setsCovered") },
          { value: t("stats.realTime"), label: t("stats.priceUpdates") },
          { value: "97.5%", label: t("stats.marketCoverage") },
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
            <div className="preview-dots"><span /><span /><span /></div>
            <div className="preview-url">pokescope.zeabur.app/dashboard</div>
          </div>
          <div className="preview-body">
            <div className="preview-table">
              <div className="preview-row preview-header-row">
                {[t("dashboard.colCard"), t("dashboard.colPrice"), t("dashboard.colFairValue"), t("dashboard.colSignal"), t("dashboard.colBubble")].map(h => (
                  <div key={h} className="preview-cell">{h}</div>
                ))}
              </div>
              {[
                { name: "Charizard Gold Star \u03b4", price: "$10,500", fair: "$11,000", signal: t("dashboard.signalFair"), signalColor: "#f59e0b", bubble: t("dashboard.bubbleLow"), bubbleIcon: "\ud83d\udfe2" },
                { name: "Crystal Lugia", price: "$8,000", fair: "$10,500", signal: t("dashboard.signalUndervalued"), signalColor: "#22c55e", bubble: t("dashboard.bubbleLow"), bubbleIcon: "\ud83d\udfe2" },
                { name: "Luigi Pikachu Full Art", price: "$17,000", fair: "$12,000", signal: t("dashboard.signalOvervalued"), signalColor: "#ef4444", bubble: t("dashboard.bubbleHigh"), bubbleIcon: "\ud83d\udd34" },
                { name: "Umbreon VMAX Alt Art", price: "$3,500", fair: "$4,200", signal: t("dashboard.signalUndervalued"), signalColor: "#22c55e", bubble: t("dashboard.bubbleLow"), bubbleIcon: "\ud83d\udfe2" },
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
        <h2>{t("features.title")}</h2>
        <p className="section-sub">{t("features.subtitle")}</p>
        <div className="features-grid">
          {FEATURE_KEYS.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3>{t(`features.${f.titleKey}`)}</h3>
              <p>{t(`features.${f.descKey}`)}</p>
              <span className={`feature-tier ${f.free ? "tier-free" : "tier-pro"}`}>
                {f.free ? t("features.free") : t("features.pro")}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="pricing" id="pricing">
        <h2>{t("pricing.title")}</h2>
        <p className="section-sub">{t("pricing.subtitle")}</p>
        <div className="pricing-grid">
          {tiers.map((tier, i) => (
            <div key={i} className={`pricing-card ${tier.highlight ? "pricing-highlight" : ""}`}>
              {tier.highlight && <div className="pricing-popular">{t("pricing.mostPopular")}</div>}
              <h3>{tier.name}</h3>
              <div className="pricing-price">
                <span className="pricing-amount">{tier.price}</span>
                <span className="pricing-period">{tier.period}</span>
              </div>
              <button
                className={tier.highlight ? "btn-primary" : "btn-secondary"}
                onClick={() => {
                  if (tier.tier) {
                    navigate(isDevMode ? `${dashPath}?upgrade=${tier.tier}` : `/sign-up?redirect_url=${dashPath}?upgrade=${tier.tier}`);
                  } else {
                    navigate(signUpPath);
                  }
                }}
              >
                {tier.cta}
              </button>
              <ul className="pricing-features">
                {(tier.features || []).map((f, j) => (
                  <li key={j} className="pricing-yes">{f}</li>
                ))}
                {(tier.limits || []).map((f, j) => (
                  <li key={`n${j}`} className="pricing-no">{f}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="final-cta">
        <h2>{t("cta.title")}</h2>
        <p>{t("cta.subtitle")}</p>
        <button className="btn-primary btn-lg" onClick={() => navigate(signUpPath)}>
          {t("cta.button")}
        </button>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-brand">
          <span>&#9889;</span> POK&Eacute;SCOPE
        </div>
        <p>{t("footer")}</p>
      </footer>
    </div>
  );
}
