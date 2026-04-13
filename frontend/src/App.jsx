import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation, LANGS, langPrefix } from "./i18n/index.jsx";
import "./App.css";

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const isDevMode = !clerkKey || clerkKey === "pk_test_PLACEHOLDER";
const API_BASE = import.meta.env.VITE_API_URL || "";

let useClerkUser, useClerkAuth;
if (!isDevMode) {
  const clerk = await import("@clerk/clerk-react");
  useClerkUser = clerk.useUser;
  useClerkAuth = clerk.useAuth;
}

const ERAS = ["All", "WOTC", "Gold Star", "e-Series", "Promo", "Modern", "Classic"];
const CARD_LANGS = ["All", "EN", "JP"];

function getSortOptions(t) {
  return [
    { key: "bubble", label: t("dashboard.sortBubble") },
    { key: "undervalued", label: t("dashboard.sortUndervalued") },
    { key: "overvalued", label: t("dashboard.sortOvervalued") },
    { key: "social", label: t("dashboard.sortSocial") },
    { key: "appreciation", label: t("dashboard.sortAppreciation") },
    { key: "scarcity", label: t("dashboard.sortScarcity") },
    { key: "price", label: t("dashboard.sortPrice") },
  ];
}

function getValuation(card, t) {
  if (!card.price || !card.fair_value) return { label: "N/A", color: "#6b7280", bg: "rgba(107,114,128,0.1)" };
  const diff = (card.price - card.fair_value) / card.fair_value;
  if (diff > 0.15) return { label: t("dashboard.signalOvervalued"), color: "#ef4444", bg: "rgba(239,68,68,0.1)" };
  if (diff < -0.15) return { label: t("dashboard.signalUndervalued"), color: "#22c55e", bg: "rgba(34,197,94,0.1)" };
  return { label: t("dashboard.signalFair"), color: "#f59e0b", bg: "rgba(245,158,11,0.1)" };
}

function getBubbleRisk(val, t) {
  if (val == null) return { label: "N/A", color: "#6b7280", icon: "\u26aa" };
  if (val > 0.3) return { label: t("dashboard.bubbleHigh"), color: "#ef4444", icon: "\ud83d\udd34" };
  if (val > 0.1) return { label: t("dashboard.bubbleModerate"), color: "#f59e0b", icon: "\ud83d\udfe1" };
  return { label: t("dashboard.bubbleLow"), color: "#22c55e", icon: "\ud83d\udfe2" };
}

function getScarcity(pop, t) {
  if (pop == null) return { label: "N/A", color: "#6b7280" };
  if (pop <= 50) return { label: t("dashboard.scarcityUltraRare"), color: "#a855f7" };
  if (pop <= 100) return { label: t("dashboard.scarcityVeryScarce"), color: "#6366f1" };
  if (pop <= 300) return { label: t("dashboard.scarcityScarce"), color: "#3b82f6" };
  if (pop <= 600) return { label: t("dashboard.scarcityModerate"), color: "#f59e0b" };
  return { label: t("dashboard.scarcityCommon"), color: "#6b7280" };
}

function Badge({ label, color, bg }) {
  return (
    <span className="badge" style={{ color, background: bg || `${color}18`, border: `1px solid ${color}30` }}>
      {label}
    </span>
  );
}

function MiniBar({ value, max, color }) {
  return (
    <div className="mini-bar-track">
      <div className="mini-bar-fill" style={{ width: `${Math.min((value / max) * 100, 100)}%`, background: color }} />
    </div>
  );
}

function Sparkline({ prices, color }) {
  const valid = prices.filter(p => p != null);
  if (valid.length < 2) return null;
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const range = max - min || 1;
  const h = 28, w = 80;
  const points = valid.map((p, i) => `${(i / (valid.length - 1)) * w},${h - ((p - min) / range) * h}`).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={w} cy={h - ((valid[valid.length - 1] - min) / range) * h} r="2.5" fill={color} />
    </svg>
  );
}

function getAnalysis(card) {
  const valueDiff = card.fair_value ? ((card.price - card.fair_value) / card.fair_value * 100).toFixed(1) : 0;
  const ret12m = card.price_12mo ? ((card.price - card.price_12mo) / card.price_12mo * 100).toFixed(1) : 0;
  const pop = card.psa10_pop || 0;

  if (Number(valueDiff) < -15) {
    return `${card.name} appears undervalued by ${Math.abs(Number(valueDiff))}% relative to fair market value. With a PSA 10 population of only ${pop.toLocaleString()} and a ${ret12m}% 12-month return, the scarcity-to-price ratio suggests significant upside potential. ${(card.social_score || 0) > 75 ? "Strong social media interest supports continued demand." : "Social engagement is currently low \u2014 watch for catalysts."}`;
  }
  if (Number(valueDiff) > 15) {
    return `${card.name} is trading ${valueDiff}% above estimated fair value. ${pop > 500 ? `The high PSA 10 population of ${pop.toLocaleString()} limits scarcity premium.` : "Scarcity supports some premium, but current pricing appears stretched."} ${(card.bubble || 0) > 0.2 ? "Bubble risk is elevated \u2014 consider waiting for a correction before entering." : "Monitor for stabilization before adding."}`;
  }
  return `${card.name} is trading near fair value. ${pop < 100 ? `With only ${pop} PSA 10 copies, long-term scarcity dynamics are favorable.` : "Population is moderate \u2014 focus on grade quality and presentation."} ${Number(ret12m) > 30 ? "Strong recent momentum suggests continued collector interest." : "Steady appreciation with moderate volatility."}`;
}

function DetailPanel({ card }) {
  const { t } = useTranslation();
  const valuation = getValuation(card, t);
  const bubble = getBubbleRisk(card.bubble, t);
  const scarcity = getScarcity(card.psa10_pop, t);
  const ret12m = card.price_12mo ? ((card.price - card.price_12mo) / card.price_12mo * 100).toFixed(1) : "N/A";
  const ret6m = card.price_6mo ? ((card.price - card.price_6mo) / card.price_6mo * 100).toFixed(1) : "N/A";
  const valueDiff = card.fair_value ? ((card.price - card.fair_value) / card.fair_value * 100).toFixed(1) : "0";
  const pricePerPop = card.psa10_pop ? (card.price / card.psa10_pop).toFixed(0) : "N/A";

  const metrics = [
    { label: t("detail.psa10pop"), value: card.psa10_pop?.toLocaleString() || "N/A", sub: scarcity.label, subColor: scarcity.color },
    { label: t("detail.psa9pop"), value: card.psa9_pop?.toLocaleString() || "N/A", sub: card.psa10_pop && card.psa9_pop ? `${(card.psa10_pop / card.psa9_pop * 100).toFixed(1)}% ${t("detail.upgradeRate")}` : "", subColor: "#6b7280" },
    { label: t("detail.pricePopRatio"), value: pricePerPop !== "N/A" ? `$${pricePerPop}` : "N/A", sub: Number(pricePerPop) > 100 ? t("detail.strongValue") : t("detail.weakScarcity"), subColor: Number(pricePerPop) > 100 ? "#22c55e" : "#f59e0b" },
    { label: t("detail.return12m"), value: ret12m !== "N/A" ? `${Number(ret12m) >= 0 ? "+" : ""}${ret12m}%` : "N/A", sub: ret6m !== "N/A" ? `6m: ${Number(ret6m) >= 0 ? "+" : ""}${ret6m}%` : "", subColor: Number(ret12m) >= 0 ? "#22c55e" : "#ef4444", valueColor: Number(ret12m) >= 0 ? "#22c55e" : "#ef4444" },
    { label: t("detail.socialScore"), value: card.social_score != null ? `${card.social_score}/100` : "N/A", sub: card.social_score > 80 ? t("detail.highBuzz") : card.social_score > 60 ? t("detail.moderateBuzz") : t("detail.lowBuzz"), subColor: card.social_score > 80 ? "#6366f1" : "#6b7280" },
    { label: t("detail.bubbleRisk"), value: `${bubble.icon} ${bubble.label}`, sub: card.bubble != null ? `Score: ${(card.bubble * 100).toFixed(0)}%` : "", subColor: bubble.color },
  ];

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <div>
          <div className="detail-title">
            {card.image_small && <img src={card.image_small} alt="" className="card-thumb" />}
            <h2>{card.name}</h2>
            <Badge label={valuation.label} color={valuation.color} />
          </div>
          <p className="detail-subtitle">{card.set_name} {card.number ? `\u00b7 ${card.number}` : ""} \u00b7 {card.lang || "EN"} \u00b7 {card.grade || "Ungraded"}</p>
        </div>
        <div className="detail-price">
          <div className="price-value">${card.price?.toLocaleString() || "N/A"}</div>
          <div className="price-diff" style={{ color: Number(valueDiff) > 0 ? "#ef4444" : "#22c55e" }}>
            {Number(valueDiff) > 0 ? "+" : ""}{valueDiff}% {t("dashboard.vsFairValue")} (${card.fair_value?.toLocaleString() || "N/A"})
          </div>
        </div>
      </div>

      <div className="detail-grid">
        {metrics.map((m, i) => (
          <div key={i} className="detail-metric">
            <div className="metric-label">{m.label}</div>
            <div className="metric-value" style={{ color: m.valueColor || "#fff" }}>{m.value}</div>
            <div className="metric-sub" style={{ color: m.subColor }}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="ai-analysis">
        <div className="ai-label">{t("dashboard.aiAnalysis")}</div>
        <p>{getAnalysis(card)}</p>
      </div>
    </div>
  );
}

function UserMenu() {
  const navigate = useNavigate();

  if (isDevMode) {
    return (
      <div className="user-menu">
        <span className="user-plan-badge free">FREE</span>
        <button className="btn-upgrade" onClick={() => navigate("/#pricing")}>Upgrade</button>
      </div>
    );
  }

  const { user } = useClerkUser();
  const { signOut } = useClerkAuth();

  const handleUpgrade = async (tier = "pro") => {
    try {
      const res = await fetch(`${API_BASE}/api/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch (e) {
      console.error("Checkout failed:", e);
    }
  };

  return (
    <div className="user-menu">
      <span className="user-plan-badge free">FREE</span>
      <button className="btn-upgrade" onClick={() => handleUpgrade("pro")}>Upgrade to Pro</button>
      <span className="user-name">{user?.firstName || user?.emailAddresses?.[0]?.emailAddress || "User"}</span>
      <button className="btn-signout" onClick={() => signOut(() => navigate("/"))}>Sign Out</button>
    </div>
  );
}

export default function App() {
  const { t, lang } = useTranslation();
  const [cards, setCards] = useState([]);
  const [stats, setStats] = useState({ undervalued: 0, overvalued: 0, bubble_risk: 0, avg_return: 0 });
  const [sortBy, setSortBy] = useState("bubble");
  const [filterEra, setFilterEra] = useState("All");
  const [filterLang, setFilterLang] = useState("All");
  const [search, setSearch] = useState("");
  const [selectedCard, setSelectedCard] = useState(null);
  const [modalImg, setModalImg] = useState(null);
  const [loading, setLoading] = useState(true);

  // Handle ?upgrade=pro or ?upgrade=dealer from pricing page
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const upgradeTier = params.get("upgrade");
    if (upgradeTier && (upgradeTier === "pro" || upgradeTier === "dealer")) {
      // Clean up URL
      window.history.replaceState({}, "", "/dashboard");
      // Trigger Stripe checkout
      fetch(`${API_BASE}/api/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier: upgradeTier }),
      })
        .then(r => r.json())
        .then(data => { if (data.url) window.location.href = data.url; })
        .catch(e => console.error("Checkout failed:", e));
    }
  }, []);

  const fetchCards = useCallback(async () => {
    const params = new URLSearchParams({ sort: sortBy, limit: "200" });
    if (filterEra !== "All") params.set("era", filterEra);
    if (filterLang !== "All") params.set("lang", filterLang);
    if (search.trim()) params.set("q", search.trim());

    try {
      const res = await fetch(`${API_BASE}/api/cards/market?${params}`);
      const data = await res.json();
      setCards(data.cards || []);
    } catch (e) {
      console.error("Failed to fetch cards:", e);
    }
    setLoading(false);
  }, [sortBy, filterEra, filterLang, search]);

  useEffect(() => {
    fetchCards();
  }, [fetchCards]);

  useEffect(() => {
    fetch(`${API_BASE}/api/cards/stats`)
      .then(r => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const statItems = [
    { label: t("dashboard.undervalued"), value: stats.undervalued, color: "#22c55e", suffix: ` ${t("dashboard.cards")}`, sortKey: "undervalued" },
    { label: t("dashboard.overvalued"), value: stats.overvalued, color: "#ef4444", suffix: ` ${t("dashboard.cards")}`, sortKey: "overvalued" },
    { label: t("dashboard.bubbleRisk"), value: stats.bubble_risk, color: "#f59e0b", suffix: ` ${t("dashboard.cards")}`, sortKey: "bubble" },
    { label: t("dashboard.avg12mReturn"), value: `${(stats.avg_return * 100).toFixed(0)}%`, color: stats.avg_return > 0 ? "#22c55e" : "#ef4444", suffix: "", sortKey: "appreciation" },
  ];
  const sortOptions = getSortOptions(t);

  return (
    <div>
      {/* Header */}
      <div className="header">
        <div className="header-inner">
          <div className="header-brand">
            <span style={{ fontSize: 22 }}>&#9889;</span>
            <div>
              <h1>POK&Eacute;SCOPE</h1>
              <p>{t("dashboard.tagline")}</p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div className="header-status">
              <span className="status-dot" />
              {t("dashboard.live")} &middot; {cards.length} {t("dashboard.cardsTracked")}
            </div>
            <UserMenu />
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        {statItems.map((s, i) => (
          <div key={i} className={`stat-item ${sortBy === s.sortKey ? "active" : ""}`} onClick={() => setSortBy(s.sortKey)}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ color: s.color }}>
              {s.value}{s.suffix}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="filters">
        <input
          type="text"
          className="search-input"
          placeholder={t("dashboard.searchPlaceholder")}
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="filter-group">
          {ERAS.map(e => (
            <button key={e} className={`filter-btn ${filterEra === e ? "active" : ""}`} onClick={() => setFilterEra(e)}>
              {e}
            </button>
          ))}
        </div>
        <div className="filter-group">
          {CARD_LANGS.map(l => (
            <button key={l} className={`filter-btn ${filterLang === l ? "active" : ""}`} onClick={() => setFilterLang(l)}>
              {l}
            </button>
          ))}
        </div>
        <select className="sort-select" value={sortBy} onChange={e => setSortBy(e.target.value)}>
          {sortOptions.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading">{t("dashboard.loading")}</div>
      ) : (
        <div className="table-wrap">
          <table className="card-table">
            <thead>
              <tr>
                {[t("dashboard.colCard"), t("dashboard.colEra"), t("dashboard.colGrade"), t("dashboard.colPrice"), t("dashboard.colFairValue"), t("dashboard.colSignal"), t("dashboard.colPsa10"), t("dashboard.colScarcity"), t("dashboard.col12mTrend"), t("dashboard.col12mReturn"), t("dashboard.colSocial"), t("dashboard.colBubble")].map(h => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cards.map(card => {
                const valuation = getValuation(card, t);
                const bubble = getBubbleRisk(card.bubble, t);
                const scarcity = getScarcity(card.psa10_pop, t);
                const ret12m = card.price_12mo ? ((card.price - card.price_12mo) / card.price_12mo * 100).toFixed(0) : null;
                const prices = [card.price_12mo, card.price_6mo, card.price_6mo && card.price ? (card.price_6mo + card.price) / 2 : null, card.price];
                const trendColor = card.price > (card.price_12mo || 0) ? "#22c55e" : "#ef4444";

                return (
                  <tr
                    key={card.id}
                    className={selectedCard?.id === card.id ? "selected" : ""}
                    onClick={() => setSelectedCard(selectedCard?.id === card.id ? null : card)}
                  >
                    <td>
                      <div className="card-cell">
                        {card.image_small && (
                          <img
                            src={card.image_small}
                            alt=""
                            className="card-thumb"
                            loading="lazy"
                            onClick={e => { e.stopPropagation(); setModalImg(card.image_large || card.image_small); }}
                          />
                        )}
                        <div>
                          <div className="card-name">{card.name}</div>
                          <div className="card-set">{card.set_name} {card.number ? `\u00b7 ${card.number}` : ""}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="era-badge">{card.era || "\u2014"}</span>
                      <span className={`lang-badge lang-${card.lang || "EN"}`}>{card.lang || "EN"}</span>
                    </td>
                    <td style={{ fontSize: 10, color: "#9ca3af" }}>{card.grade || "\u2014"}</td>
                    <td style={{ fontWeight: 700, color: "#fff", fontFamily: "'Space Grotesk', sans-serif" }}>
                      ${card.price?.toLocaleString() || "\u2014"}
                    </td>
                    <td style={{ color: "#9ca3af" }}>${card.fair_value?.toLocaleString() || "\u2014"}</td>
                    <td><Badge label={valuation.label} color={valuation.color} /></td>
                    <td>
                      <span style={{ color: card.psa10_pop <= 100 ? "#a855f7" : "#9ca3af", fontWeight: card.psa10_pop <= 100 ? 600 : 400 }}>
                        {card.psa10_pop?.toLocaleString() || "\u2014"}
                      </span>
                    </td>
                    <td><Badge label={scarcity.label} color={scarcity.color} /></td>
                    <td><Sparkline prices={prices} color={trendColor} /></td>
                    <td style={{ fontWeight: 600, color: ret12m != null ? (Number(ret12m) >= 0 ? "#22c55e" : "#ef4444") : "#6b7280" }}>
                      {ret12m != null ? `${Number(ret12m) >= 0 ? "+" : ""}${ret12m}%` : "\u2014"}
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <MiniBar value={card.social_score || 0} max={100} color={card.social_score > 80 ? "#6366f1" : "#4b5563"} />
                        <span style={{ fontSize: 10, color: card.social_score > 80 ? "#a5b4fc" : "#6b7280" }}>{card.social_score ?? "\u2014"}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: 10 }}>{bubble.icon}</span>
                      <span style={{ fontSize: 10, marginLeft: 4, color: bubble.color, fontWeight: 600 }}>{bubble.label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Panel */}
      {selectedCard && <DetailPanel card={selectedCard} />}

      {/* Image Modal */}
      {modalImg && (
        <div className="modal-overlay" onClick={() => setModalImg(null)}>
          <img src={modalImg} alt="Card" />
        </div>
      )}

      {/* Footer */}
      <div className="footer">
        POK&Eacute;SCOPE MVP &middot; Data sourced from eBay, Fanatics Collect, PriceCharting, PSA Pop Reports &middot; Not financial advice &middot; Built for collectors, by collectors
      </div>
    </div>
  );
}
