import { useState, useEffect } from "react";
import { useApp } from "../contexts/AppContext";
import { investmentAPI } from "../services/api";
import CandleLoader from "../components/ui/CandleLoader";

export default function Investment({ userId }) {
  const { language } = useApp();
  const [commodities, setCommodities] = useState([]);
  const [mutualFunds, setMutualFunds] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [tab, setTab] = useState("commodities"); // "commodities" | "mutualfunds"
  const [error, setError] = useState("");

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [comRes, mfRes] = await Promise.allSettled([
        investmentAPI.getCommodities(),
        investmentAPI.getPopularMutualFunds(),
      ]);
      if (comRes.status === 'fulfilled') setCommodities(comRes.value?.commodities || comRes.value || []);
      if (mfRes.status === 'fulfilled') setMutualFunds(mfRes.value?.funds || mfRes.value || []);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await investmentAPI.searchMutualFunds(searchQuery);
      setSearchResults(res.results || res || []);
    } catch (e) { setError(e.message); }
    setSearching(false);
  };

  const formatPrice = (val) => {
    if (!val) return '—';
    return typeof val === 'number' ? `₹${val.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : `₹${val}`;
  };

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
          📈 {language === 'hi' ? 'निवेश' : 'Investments'}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {language === 'hi' ? 'लाइव कमोडिटी दरें और म्यूचुअल फंड' : 'Live commodity prices & mutual fund data'}
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
        <button onClick={() => setTab("commodities")}
          style={{ padding: '0.5rem 1.25rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', cursor: 'pointer',
            background: tab === 'commodities' ? 'var(--accent-primary)' : 'var(--card-bg)', color: tab === 'commodities' ? '#fff' : 'var(--text-primary)', fontSize: '0.85rem' }}>
          🥇 {language === 'hi' ? 'कमोडिटी' : 'Commodities'}
        </button>
        <button onClick={() => setTab("mutualfunds")}
          style={{ padding: '0.5rem 1.25rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', cursor: 'pointer',
            background: tab === 'mutualfunds' ? 'var(--accent-primary)' : 'var(--card-bg)', color: tab === 'mutualfunds' ? '#fff' : 'var(--text-primary)', fontSize: '0.85rem' }}>
          📊 {language === 'hi' ? 'म्यूचुअल फंड' : 'Mutual Funds'}
        </button>
      </div>

      {error && <p style={{ color: '#e74c3c', marginBottom: '1rem' }}>{error}</p>}

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'डेटा लोड हो रहा है...' : 'Loading market data...'} />
      ) : tab === "commodities" ? (
        /* Commodities */
        <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fill, minmax(min(280px, 100%), 1fr))' }}>
          {commodities.map((c, i) => (
            <div key={i} style={{ background: 'var(--card-bg)', borderRadius: '16px', padding: '1.25rem', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>
                    {(c.commodity || c.name || '').toLowerCase() === 'gold' ? '🥇' : (c.commodity || c.name || '').toLowerCase() === 'silver' ? '🥈' : (c.commodity || c.name || '').toLowerCase() === 'crude_oil' ? '🛢️' : '🔥'} {c.name || c.commodity}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{c.symbol || ''}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{formatPrice(c.price_inr || c.price || c.current_price)}</div>
                  {(c.change_pct !== undefined || c.change_percent !== undefined) && (
                    <span style={{ color: (c.change_pct || c.change_percent || 0) >= 0 ? '#2ecc71' : '#e74c3c', fontSize: '0.85rem', fontWeight: 600 }}>
                      {(c.change_pct || c.change_percent || 0) >= 0 ? '▲' : '▼'} {Math.abs(c.change_pct || c.change_percent || 0).toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
              {c.unit && <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>per {c.unit}</p>}
            </div>
          ))}
          {commodities.length === 0 && (
            <p style={{ color: 'var(--text-secondary)' }}>
              {language === 'hi' ? 'कोई कमोडिटी डेटा उपलब्ध नहीं' : 'No commodity data available'}
            </p>
          )}
        </div>
      ) : (
        /* Mutual Funds */
        <div>
          {/* Search bar */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <input type="text" placeholder={language === 'hi' ? 'म्यूचुअल फंड खोजें...' : 'Search mutual funds...'}
              value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              style={{ flex: 1, padding: '0.7rem 1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.9rem' }} />
            <button onClick={handleSearch} disabled={searching}
              style={{ padding: '0.7rem 1.25rem', borderRadius: '10px', background: 'var(--accent-primary)', color: '#fff', border: 'none', cursor: 'pointer', fontSize: '0.9rem' }}>
              {searching ? '...' : '🔍'}
            </button>
          </div>

          {/* Search results */}
          {searchResults.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>{language === 'hi' ? 'खोज परिणाम' : 'Search Results'}</h3>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {searchResults.slice(0, 10).map((fund, i) => (
                  <div key={i} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{fund.schemeName || fund.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{fund.fundHouse || fund.category || ''}</div>
                    </div>
                    {fund.nav && <div style={{ fontWeight: 'bold' }}>NAV: ₹{fund.nav}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Popular funds */}
          <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>
            {language === 'hi' ? 'लोकप्रिय म्यूचुअल फंड' : 'Popular Mutual Funds'}
          </h3>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {mutualFunds.map((fund, i) => (
              <div key={i} style={{ background: 'var(--card-bg)', borderRadius: '12px', padding: '1rem', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1, marginRight: '1rem' }}>
                    <h4 style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>{fund.scheme_name || fund.name}</h4>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{fund.fund_house || fund.category || ''}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '1.05rem' }}>₹{fund.nav || fund.current_nav || '—'}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>NAV</div>
                  </div>
                </div>
              </div>
            ))}
            {mutualFunds.length === 0 && (
              <p style={{ color: 'var(--text-secondary)' }}>
                {language === 'hi' ? 'कोई म्यूचुअल फंड डेटा नहीं' : 'No mutual fund data available'}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

