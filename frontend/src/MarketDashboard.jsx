import { useState, useEffect } from 'react';
import { useTranslation } from './i18n/index.jsx';

export default function MarketDashboard() {
  const [data, setData] = useState(null);
  const { t } = useTranslation();

  useEffect(() => {
    async function load() {
      const [socialRes, priceRes, statsRes] = await Promise.all([
        fetch('/api/cards/market?sort=social&limit=200'),
        fetch('/api/cards/market?sort=price&limit=200'),
        fetch('/api/cards/stats'),
      ]);
      const [socialData, priceData, stats] = await Promise.all([
        socialRes.json(), priceRes.json(), statsRes.json(),
      ]);

      const cards = priceData.cards;
      const totalMarketValue = cards.reduce((s, c) => s + (c.price || 0), 0);
      const totalFairValue = cards.reduce((s, c) => s + (c.fair_value || 0), 0);

      const hotCards = socialData.cards.slice(0, 5);
      const gainers = [...cards]
        .filter(c => c.price_12mo > 0)
        .sort((a, b) =>
          (b.price - b.price_12mo) / b.price_12mo -
          (a.price - a.price_12mo) / a.price_12mo
        )
        .slice(0, 5);

      const sentimentPct = Math.round(
        stats.undervalued / (stats.undervalued + stats.overvalued) * 100
      );

      setData({
        totalMarketValue, totalFairValue, hotCards, gainers,
        totalCards: priceData.total, sentimentPct,
        avgReturn: stats.avg_return, bubbleRisk: stats.bubble_risk,
      });
    }
    load();
  }, []);

  if (!data) return null;

  const fmt = n => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : `$${(n/1e3).toFixed(0)}K`;
  const diffPct = ((data.totalMarketValue - data.totalFairValue) / data.totalFairValue * 100).toFixed(1);
  const sentimentLabel = data.sentimentPct > 55 ? "Buyer's Market" : data.sentimentPct < 45 ? "Seller's Market" : 'Neutral';
  const sentimentColor = data.sentimentPct > 55 ? '#22c55e' : data.sentimentPct < 45 ? '#ef4444' : '#f59e0b';

  return (
    <section className="market-dash">
      <div className="dash-inner">
        <div className="dash-section-header">
          <div className="dash-section-badge">LIVE MARKET PULSE</div>
          <h2 className="dash-section-title">Today's Market at a Glance</h2>
          <p className="dash-section-sub">Real-time intelligence from 20,000+ tracked Pok&eacute;mon cards</p>
        </div>

        <div className="dash-stats-row">
          <div className="dash-stat">
            <div className="dash-stat-label">TOP 200 MARKET CAP</div>
            <div className="dash-stat-value">{fmt(data.totalMarketValue)}</div>
            <div className="dash-stat-sub" style={{ color: data.totalMarketValue < data.totalFairValue ? '#22c55e' : '#ef4444' }}>
              {diffPct}% vs fair value
            </div>
          </div>
          <div className="dash-stat">
            <div className="dash-stat-label">CARDS TRACKED</div>
            <div className="dash-stat-value">{data.totalCards.toLocaleString()}</div>
            <div className="dash-stat-sub" style={{ color: '#a5b4fc' }}>Across all eras</div>
          </div>
          <div className="dash-stat">
            <div className="dash-stat-label">MARKET SENTIMENT</div>
            <div className="dash-stat-value" style={{ color: sentimentColor }}>{sentimentLabel}</div>
            <div className="dash-stat-sub">{data.sentimentPct}% of cards undervalued</div>
          </div>
          <div className="dash-stat">
            <div className="dash-stat-label">AVG 12M RETURN</div>
            <div className="dash-stat-value" style={{ color: '#22c55e' }}>+{(data.avgReturn * 100).toFixed(1)}%</div>
            <div className="dash-stat-sub">{data.bubbleRisk.toLocaleString()} cards at bubble risk</div>
          </div>
        </div>

        <div className="dash-columns">
          <div className="dash-column-main">
            <div className="dash-col-header">
              <span className="dash-col-icon">&#128293;</span>
              <span className="dash-col-title">Trending Now</span>
              <span className="dash-col-badge">By Social Buzz</span>
            </div>
            <div className="dash-cards-grid">
              {data.hotCards.map(c => {
                const bubbleColor = c.bubble > 0.3 ? '#ef4444' : c.bubble < -0.1 ? '#22c55e' : '#f59e0b';
                const bubbleLabel = c.bubble > 0.3 ? 'HIGH' : c.bubble < -0.1 ? 'LOW' : 'MED';
                return (
                  <div className="dash-card" key={c.id}>
                    <div className="dash-card-img-wrap">
                      <img src={c.image_small} alt={c.name} className="dash-card-img" />
                      <div className="dash-card-buzz">{c.social_score}/100</div>
                    </div>
                    <div className="dash-card-info">
                      <div className="dash-card-name">{c.name}</div>
                      <div className="dash-card-set">{c.set_name}</div>
                      <div className="dash-card-price">${c.price.toLocaleString()}</div>
                      <div className="dash-card-bubble" style={{ color: bubbleColor }}>Bubble: {bubbleLabel}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="dash-column-side">
            <div className="dash-col-header">
              <span className="dash-col-icon">&#128200;</span>
              <span className="dash-col-title">Top Gainers</span>
              <span className="dash-col-badge">12M Return</span>
            </div>
            <div className="dash-gainers-list">
              {data.gainers.map((c, i) => {
                const ret = Math.round((c.price - c.price_12mo) / c.price_12mo * 100);
                return (
                  <div className="dash-gainer" key={c.id}>
                    <span className="dash-gainer-rank">{i + 1}</span>
                    <img src={c.image_small} alt={c.name} className="dash-gainer-img" />
                    <div className="dash-gainer-info">
                      <div className="dash-gainer-name">{c.name}</div>
                      <div className="dash-gainer-set">{c.set_name}</div>
                    </div>
                    <div className="dash-gainer-stats">
                      <div className="dash-gainer-price">${c.price.toLocaleString()}</div>
                      <div className="dash-gainer-ret" style={{ color: '#22c55e' }}>+{ret}%</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
