import { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../store/authStore.jsx';
import { portfolioAPI, investmentAPI } from '../services/api';
import CandleLoader from '../components/ui/CandleLoader';

export default function Portfolio({ userId: propUserId }) {
  const { language } = useApp();
  const auth = useAuth();
  const userId = propUserId || auth.userId;

  const [portfolio, setPortfolio] = useState(null);
  const [commodities, setCommodities] = useState([]);
  const [mutualFunds, setMutualFunds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('holdings'); // holdings | buy
  const [buyTab, setBuyTab] = useState('commodity'); // commodity | mutual_fund
  const [buyQty, setBuyQty] = useState('');
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [actionMsg, setActionMsg] = useState('');
  const [acting, setActing] = useState(false);
  const [sellModal, setSellModal] = useState(null);
  const [sellQty, setSellQty] = useState('');

  useEffect(() => { if (userId) loadAll(); }, [userId]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [pRes, cRes, mRes] = await Promise.allSettled([
        portfolioAPI.getPortfolio(userId),
        investmentAPI.getCommodities(),
        investmentAPI.getPopularMutualFunds(),
      ]);
      if (pRes.status === 'fulfilled') setPortfolio(pRes.value);
      if (cRes.status === 'fulfilled') setCommodities(cRes.value?.commodities || cRes.value || []);
      if (mRes.status === 'fulfilled') setMutualFunds(mRes.value?.funds || mRes.value || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fmt = (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

  const handleBuy = async () => {
    if (!selectedAsset || !buyQty || Number(buyQty) <= 0) return;
    setActing(true);
    setActionMsg('');
    try {
      const res = await portfolioAPI.buy(
        userId,
        selectedAsset.type,
        selectedAsset.symbol,
        selectedAsset.name,
        Number(buyQty),
        language,
      );
      setActionMsg(res.message || 'Purchase successful!');
      setBuyQty('');
      setSelectedAsset(null);
      await loadAll();
    } catch (e) { setActionMsg(e.message || 'Purchase failed'); }
    setActing(false);
  };

  const handleSell = async () => {
    if (!sellModal || !sellQty || Number(sellQty) <= 0) return;
    setActing(true);
    setActionMsg('');
    try {
      const res = await portfolioAPI.sell(userId, sellModal.id, Number(sellQty), language);
      setActionMsg(res.message || 'Sold successfully!');
      setSellModal(null);
      setSellQty('');
      await loadAll();
    } catch (e) { setActionMsg(e.message || 'Sell failed'); }
    setActing(false);
  };

  const cardStyle = { background: 'var(--card-bg)', borderRadius: '16px', padding: '1.25rem', border: '1px solid var(--border-subtle)' };
  const btnBase = { padding: '0.5rem 1.25rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', cursor: 'pointer', fontSize: '0.85rem' };

  return (
    <div style={{ padding: '1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
          💼 {language === 'hi' ? 'वर्चुअल ट्रेडिंग' : 'Virtual Trading'}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {language === 'hi'
            ? '₹1,00,000 वर्चुअल बैलेंस से निवेश सीखें'
            : 'Learn to invest with ₹1,00,000 virtual balance'}
        </p>
      </div>

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'लोड हो रहा है...' : 'Loading portfolio...'} />
      ) : (
        <>
          {/* ── Summary Cards ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(160px, 100%), 1fr))', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div style={{ ...cardStyle, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'वर्चुअल बैलेंस' : 'Virtual Balance'}</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{fmt(portfolio?.virtual_balance ?? 100000)}</div>
            </div>
            <div style={{ ...cardStyle, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'निवेशित' : 'Invested'}</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 'bold' }}>{fmt(portfolio?.total_invested ?? 0)}</div>
            </div>
            <div style={{ ...cardStyle, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'वर्तमान मूल्य' : 'Current Value'}</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 'bold' }}>{fmt(portfolio?.total_current_value ?? 0)}</div>
            </div>
            <div style={{ ...cardStyle, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'लाभ/हानि' : 'P&L'}</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: (portfolio?.overall_pnl ?? 0) >= 0 ? '#2ecc71' : '#e74c3c' }}>
                {(portfolio?.overall_pnl ?? 0) >= 0 ? '+' : ''}{fmt(portfolio?.overall_pnl ?? 0)}
                <span style={{ fontSize: '0.75rem', marginLeft: '4px' }}>({(portfolio?.overall_pnl_pct ?? 0).toFixed(1)}%)</span>
              </div>
            </div>
          </div>

          {/* ── Tabs ── */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <button onClick={() => setTab('holdings')} style={{ ...btnBase, background: tab === 'holdings' ? 'var(--accent-primary)' : 'var(--card-bg)', color: tab === 'holdings' ? '#fff' : 'var(--text-primary)' }}>
              📊 {language === 'hi' ? 'होल्डिंग्स' : 'Holdings'}
            </button>
            <button onClick={() => setTab('buy')} style={{ ...btnBase, background: tab === 'buy' ? 'var(--accent-primary)' : 'var(--card-bg)', color: tab === 'buy' ? '#fff' : 'var(--text-primary)' }}>
              🛒 {language === 'hi' ? 'खरीदें' : 'Buy'}
            </button>
          </div>

          {/* ── Action message ── */}
          {actionMsg && (
            <div style={{ padding: '0.75rem 1rem', borderRadius: '10px', marginBottom: '1rem', background: actionMsg.includes('fail') || actionMsg.includes('Insufficient') ? '#fdeded' : '#edfded', color: actionMsg.includes('fail') || actionMsg.includes('Insufficient') ? '#e74c3c' : '#2ecc71', fontSize: '0.9rem' }}>
              {actionMsg}
            </div>
          )}

          {tab === 'holdings' ? (
            /* ── Holdings ── */
            <div>
              {(portfolio?.holdings || []).length > 0 ? (
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  {portfolio.holdings.map((h) => (
                    <div key={h.id} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                      <div style={{ flex: 1, minWidth: '180px' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{h.asset_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {h.quantity} units × {fmt(h.buy_price)} avg
                        </div>
                      </div>
                      <div style={{ textAlign: 'right', minWidth: '120px' }}>
                        <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{fmt(h.current_value)}</div>
                        <div style={{ fontSize: '0.8rem', color: h.pnl >= 0 ? '#2ecc71' : '#e74c3c', fontWeight: 600 }}>
                          {h.pnl >= 0 ? '▲' : '▼'} {fmt(Math.abs(h.pnl))} ({h.pnl_pct.toFixed(1)}%)
                        </div>
                      </div>
                      <button
                        onClick={() => { setSellModal(h); setSellQty(String(h.quantity)); }}
                        style={{ ...btnBase, background: '#e74c3c', color: '#fff', border: 'none', padding: '0.4rem 1rem' }}
                      >
                        {language === 'hi' ? 'बेचें' : 'Sell'}
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ ...cardStyle, textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</div>
                  <p>{language === 'hi' ? 'कोई होल्डिंग नहीं। Buy टैब से शुरू करें!' : 'No holdings yet. Start buying from the Buy tab!'}</p>
                </div>
              )}
            </div>
          ) : (
            /* ── Buy Tab ── */
            <div>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <button onClick={() => setBuyTab('commodity')} style={{ ...btnBase, background: buyTab === 'commodity' ? 'var(--accent-primary)' : 'var(--card-bg)', color: buyTab === 'commodity' ? '#fff' : 'var(--text-primary)' }}>
                  🥇 {language === 'hi' ? 'कमोडिटी' : 'Commodities'}
                </button>
                <button onClick={() => setBuyTab('mutual_fund')} style={{ ...btnBase, background: buyTab === 'mutual_fund' ? 'var(--accent-primary)' : 'var(--card-bg)', color: buyTab === 'mutual_fund' ? '#fff' : 'var(--text-primary)' }}>
                  📊 {language === 'hi' ? 'म्यूचुअल फंड' : 'Mutual Funds'}
                </button>
              </div>

              {/* Selected asset buy form */}
              {selectedAsset && (
                <div style={{ ...cardStyle, marginBottom: '1rem', borderColor: 'var(--accent-primary)' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                    {language === 'hi' ? 'खरीदें' : 'Buy'}: {selectedAsset.name}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                    {language === 'hi' ? 'वर्तमान कीमत' : 'Current Price'}: {fmt(selectedAsset.price)}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <input type="number" value={buyQty} onChange={(e) => setBuyQty(e.target.value)} min="0.01" step="0.01"
                      placeholder={language === 'hi' ? 'मात्रा' : 'Quantity'}
                      style={{ flex: 1, padding: '0.6rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.9rem' }} />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', minWidth: '90px' }}>
                      = {buyQty ? fmt(Number(buyQty) * selectedAsset.price) : '₹0'}
                    </span>
                    <button onClick={handleBuy} disabled={acting || !buyQty}
                      style={{ ...btnBase, background: 'var(--accent-primary)', color: '#fff', border: 'none', opacity: acting ? 0.6 : 1 }}>
                      {acting ? '...' : language === 'hi' ? '✓ खरीदें' : '✓ Buy'}
                    </button>
                    <button onClick={() => { setSelectedAsset(null); setBuyQty(''); }}
                      style={{ ...btnBase, background: 'transparent', color: 'var(--text-secondary)' }}>✕</button>
                  </div>
                </div>
              )}

              {/* Asset list */}
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {buyTab === 'commodity' ? commodities.map((c, i) => {
                  const price = c.price_inr || c.price || c.current_price || 0;
                  const sym = c.commodity || c.name?.toLowerCase().replace(/\s/g, '_') || '';
                  return (
                    <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', transition: 'border-color 0.2s' }}
                      onClick={() => setSelectedAsset({ type: 'commodity', symbol: sym, name: c.name || c.commodity, price })}>
                      <div>
                        <span style={{ fontWeight: 600 }}>{c.name === 'gold' || c.commodity === 'gold' ? '🥇' : c.name === 'silver' || c.commodity === 'silver' ? '🥈' : '🛢️'} {c.name || c.commodity}</span>
                        {c.change_pct !== undefined && (
                          <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: c.change_pct >= 0 ? '#2ecc71' : '#e74c3c' }}>
                            {c.change_pct >= 0 ? '▲' : '▼'} {Math.abs(c.change_pct).toFixed(2)}%
                          </span>
                        )}
                      </div>
                      <strong>{fmt(price)}</strong>
                    </div>
                  );
                }) : mutualFunds.map((mf, i) => {
                  const nav = mf.nav || mf.current_nav || 0;
                  const code = String(mf.scheme_code || mf.code || '');
                  return (
                    <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', transition: 'border-color 0.2s' }}
                      onClick={() => setSelectedAsset({ type: 'mutual_fund', symbol: code, name: mf.scheme_name || mf.name, price: Number(nav) })}>
                      <div style={{ flex: 1, marginRight: '1rem' }}>
                        <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{mf.scheme_name || mf.name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{mf.fund_house || mf.category || ''}</div>
                      </div>
                      <strong>₹{nav}</strong>
                    </div>
                  );
                })}
                {(buyTab === 'commodity' ? commodities : mutualFunds).length === 0 && (
                  <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem' }}>
                    {language === 'hi' ? 'कोई डेटा उपलब्ध नहीं' : 'No data available'}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ── Sell Modal ── */}
          {sellModal && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
              onClick={() => setSellModal(null)}>
              <div style={{ ...cardStyle, width: '90%', maxWidth: '400px', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}
                onClick={(e) => e.stopPropagation()}>
                <h3 style={{ marginBottom: '1rem' }}>
                  {language === 'hi' ? 'बेचें' : 'Sell'}: {sellModal.asset_name}
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  {language === 'hi' ? 'उपलब्ध' : 'Available'}: {sellModal.quantity} units
                </p>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                  <input type="number" value={sellQty} onChange={(e) => setSellQty(e.target.value)}
                    max={sellModal.quantity} min="0.01" step="0.01"
                    placeholder={language === 'hi' ? 'मात्रा' : 'Quantity'}
                    style={{ flex: 1, padding: '0.6rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  <button onClick={() => setSellModal(null)} style={{ ...btnBase }}>
                    {language === 'hi' ? 'रद्द करें' : 'Cancel'}
                  </button>
                  <button onClick={handleSell} disabled={acting}
                    style={{ ...btnBase, background: '#e74c3c', color: '#fff', border: 'none', opacity: acting ? 0.6 : 1 }}>
                    {acting ? '...' : language === 'hi' ? '✓ बेचें' : '✓ Sell'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

