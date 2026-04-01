import { useState, useEffect } from "react";
import { useApp } from "../contexts/AppContext";
import { useAuth } from "../store/authStore.jsx";
import { recommendationsAPI, investmentAPI } from "../services/api";
import Layout from "../components/layout/Layout";
import CandleLoader from "../components/ui/CandleLoader";
import Analytics from "./Analytics";
import Mentor from "./Mentor";
import Schemes from "./Schemes";
import Learning from "./Learning";
import Investment from "./Investment";
import Portfolio from "./Portfolio";
import FinGame from "./FinGame";
import "./Dashboard.css";

export default function Dashboard({ onLogout, initialSection }) {
  const { t, language } = useApp();
  const { userName, userId, userLevel } = useAuth();
  const [currentSection, setCurrentSection] = useState(initialSection || 'dashboard');

  // Recommendation data
  const [creditCards, setCreditCards] = useState([]);
  const [govtSchemes, setGovtSchemes] = useState([]);
  const [commodities, setCommodities] = useState([]);
  const [mutualFunds, setMutualFunds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userId) loadDashboardData();
  }, [userId, language]);

  useEffect(() => {
    if (!userId || currentSection !== 'dashboard') return;

    let cancelled = false;
    const refreshCommodities = async () => {
      try {
        const res = await investmentAPI.getCommodities({ live: true });
        if (!cancelled) setCommodities(res?.commodities || res || []);
      } catch (e) {
        if (!cancelled) console.error('Commodity refresh error', e);
      }
    };

    refreshCommodities();
    const intervalId = setInterval(refreshCommodities, 15000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [userId, currentSection]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [cardsRes, schemesRes, comRes, mfRes] = await Promise.allSettled([
        recommendationsAPI.getCreditCards(userId, language).catch(() => recommendationsAPI.getAllCards()),
        recommendationsAPI.getGovtSchemes(userId, language).catch(() => recommendationsAPI.getAllSchemes()),
        investmentAPI.getCommodities({ live: true }),
        investmentAPI.getPopularMutualFunds(),
      ]);
      if (cardsRes.status === 'fulfilled') setCreditCards(cardsRes.value?.cards || cardsRes.value || []);
      if (schemesRes.status === 'fulfilled') setGovtSchemes(schemesRes.value?.schemes || schemesRes.value || []);
      if (comRes.status === 'fulfilled') setCommodities(comRes.value?.commodities || comRes.value || []);
      if (mfRes.status === 'fulfilled') setMutualFunds(mfRes.value?.funds || mfRes.value || []);
    } catch (e) { console.error('Dashboard load error', e); }
    setLoading(false);
  };

  const handleNavigate = (section) => setCurrentSection(section);

  const renderContent = () => {
    switch (currentSection) {
      case 'analytics': return <Analytics userId={userId} />;
      case 'mentor': return <Mentor userId={userId} />;
      case 'schemes': return <Schemes userId={userId} />;
      case 'learning': return <Learning userId={userId} />;
      case 'investments': return <Investment userId={userId} />;
      case 'portfolio': return <Portfolio userId={userId} />;
      case 'fingame': return <FinGame userId={userId} onNavigate={handleNavigate} />;
      case 'dashboard':
      default:
        return renderDashboard();
    }
  };

  const fmt = (v) => {
    if (!v) return '—';
    return typeof v === 'number' ? `₹${v.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : `₹${v}`;
  };

  const cardStyle = { background: 'var(--card-bg)', borderRadius: '16px', padding: '1.25rem', border: '1px solid var(--border-subtle)' };

  const renderDashboard = () => (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <div className="header-left">
          <h1>{language === 'hi' ? 'डैशबोर्ड' : 'Dashboard'}</h1>
          <p>{language === 'hi' ? 'स्वागत है' : 'Welcome'}, {userName || 'User'}! {language === 'hi' ? 'आपके लिए व्यक्तिगत अनुशंसाएँ' : 'Personalized recommendations for you'}</p>
        </div>
      </div>

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'अनुशंसाएँ लोड हो रही हैं...' : 'Loading recommendations...'} />
      ) : (
        <div style={{ display: 'grid', gap: '1.5rem' }}>

          {/* ── Credit Cards ── */}
          <section>
            <h2 style={{ fontSize: '1.15rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               {language === 'hi' ? 'अनुशंसित क्रेडिट कार्ड' : 'Recommended Credit Cards'}
              <button onClick={() => setCurrentSection('schemes')} style={{ marginLeft: 'auto', fontSize: '0.75rem', background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.25rem 0.6rem', cursor: 'pointer', color: 'var(--accent-primary)' }}>
                {language === 'hi' ? 'सभी देखें →' : 'View All →'}
              </button>
            </h2>
            <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fill, minmax(min(300px, 100%), 1fr))' }}>
              {creditCards.slice(0, 3).map((card, i) => (
                <div key={i} style={{ ...cardStyle, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>{card.name}</h3>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{card.bank} · {card.card_type}</span>
                    </div>
                    <span style={{ background: 'var(--accent-primary)', color: '#fff', padding: '2px 8px', borderRadius: '8px', fontSize: '0.7rem', whiteSpace: 'nowrap' }}>
                      {card.annual_fee || 'Free'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{card.best_for}</p>
                  <ul style={{ paddingLeft: '1rem', fontSize: '0.78rem', lineHeight: 1.7, color: 'var(--text-primary)', margin: 0, flex: 1 }}>
                    {(card.benefits || []).slice(0, 3).map((b, j) => <li key={j}>{b}</li>)}
                  </ul>
                  {card.apply_url && (
                    <a href={card.apply_url} target="_blank" rel="noopener noreferrer"
                      style={{ display: 'inline-block', marginTop: '0.25rem', padding: '0.45rem 1rem', background: 'var(--accent-primary)', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontSize: '0.8rem', textAlign: 'center' }}>
                      {language === 'hi' ? 'अभी आवेदन करें ' : 'Apply Now '}
                    </a>
                  )}
                </div>
              ))}
              {creditCards.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', padding: '1rem' }}>
                  {language === 'hi' ? 'कोई क्रेडिट कार्ड अनुशंसा उपलब्ध नहीं' : 'No credit card recommendations available'}
                </p>
              )}
            </div>
          </section>

          {/* ── Government Schemes ── */}
          <section>
            <h2 style={{ fontSize: '1.15rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               {language === 'hi' ? 'सरकारी योजनाएँ' : 'Government Schemes'}
              <button onClick={() => setCurrentSection('schemes')} style={{ marginLeft: 'auto', fontSize: '0.75rem', background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.25rem 0.6rem', cursor: 'pointer', color: 'var(--accent-primary)' }}>
                {language === 'hi' ? 'सभी देखें →' : 'View All →'}
              </button>
            </h2>
            <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fill, minmax(min(300px, 100%), 1fr))' }}>
              {govtSchemes.slice(0, 3).map((scheme, i) => (
                <div key={i} style={{ ...cardStyle, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>
                      {scheme.name_hi && language === 'hi' ? scheme.name_hi : scheme.name}
                    </h3>
                    {scheme.category && (
                      <span style={{ background: '#2ecc71', color: '#fff', padding: '2px 8px', borderRadius: '8px', fontSize: '0.7rem', textTransform: 'capitalize', whiteSpace: 'nowrap' }}>
                        {scheme.category}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{scheme.description}</p>
                  {scheme.eligibility && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <strong>{language === 'hi' ? 'पात्रता' : 'Eligibility'}:</strong> {scheme.eligibility}
                    </div>
                  )}
                  <ul style={{ paddingLeft: '1rem', fontSize: '0.78rem', lineHeight: 1.7, color: 'var(--text-primary)', margin: 0, flex: 1 }}>
                    {(scheme.benefits || []).slice(0, 3).map((b, j) => <li key={j}>{b}</li>)}
                  </ul>
                  {scheme.apply_url && (
                    <a href={scheme.apply_url} target="_blank" rel="noopener noreferrer"
                      style={{ display: 'inline-block', marginTop: '0.25rem', padding: '0.45rem 1rem', background: '#2ecc71', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontSize: '0.8rem', textAlign: 'center' }}>
                      {language === 'hi' ? 'अभी आवेदन करें ' : 'Apply Now '}
                    </a>
                  )}
                </div>
              ))}
              {govtSchemes.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', padding: '1rem' }}>
                  {language === 'hi' ? 'कोई योजना उपलब्ध नहीं' : 'No schemes available'}
                </p>
              )}
            </div>
          </section>

          {/* ── Mutual Funds ── */}
          <section>
            <h2 style={{ fontSize: '1.15rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               {language === 'hi' ? 'लोकप्रिय म्यूचुअल फंड' : 'Popular Mutual Funds'}
              <button onClick={() => setCurrentSection('investments')} style={{ marginLeft: 'auto', fontSize: '0.75rem', background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.25rem 0.6rem', cursor: 'pointer', color: 'var(--accent-primary)' }}>
                {language === 'hi' ? 'और देखें →' : 'Explore More →'}
              </button>
            </h2>
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {mutualFunds.slice(0, 5).map((mf, i) => (
                <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.85rem 1.25rem' }}>
                  <div style={{ flex: 1, marginRight: '1rem' }}>
                    <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{mf.scheme_name || mf.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{mf.fund_house || mf.category || ''}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '1.05rem' }}>₹{mf.nav || mf.current_nav || '—'}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>NAV</div>
                  </div>
                </div>
              ))}
              {mutualFunds.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', padding: '1rem' }}>
                  {language === 'hi' ? 'कोई म्यूचुअल फंड डेटा नहीं' : 'No mutual fund data available'}
                </p>
              )}
            </div>
          </section>

          {/* ── Commodities ── */}
          <section>
            <h2 style={{ fontSize: '1.15rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               {language === 'hi' ? 'कमोडिटी बाज़ार' : 'Commodity Market'}
              <button onClick={() => setCurrentSection('investments')} style={{ marginLeft: 'auto', fontSize: '0.75rem', background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '0.25rem 0.6rem', cursor: 'pointer', color: 'var(--accent-primary)' }}>
                {language === 'hi' ? 'और देखें →' : 'Explore More →'}
              </button>
            </h2>
            <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fill, minmax(min(200px, 100%), 1fr))' }}>
              {commodities.slice(0, 4).map((c, i) => {
                const price = c.price_inr || c.price || c.current_price || 0;
                const name = c.name || c.commodity || '';
                const changePercent = c.change_pct ?? c.change_percent;
                return (
                  <div key={i} style={{ ...cardStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, marginBottom: '0.25rem', letterSpacing: '0.05em', background: 'var(--accent-primary)', color: '#fff', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.25rem' }}>
                      {name === 'gold' ? 'AU' : name === 'silver' ? 'AG' : name === 'crude_oil' ? 'OIL' : name === 'natural_gas' ? 'GAS' : name.substring(0,2).toUpperCase()}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'capitalize', marginBottom: '0.25rem' }}>
                      {name.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontWeight: 'bold', fontSize: '1.2rem', color: 'var(--accent-primary)' }}>{fmt(price)}</div>
                    {changePercent !== undefined && (
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: changePercent >= 0 ? '#2ecc71' : '#e74c3c', marginTop: '0.25rem' }}>
                        {changePercent >= 0 ? '▲' : '▼'} {Math.abs(changePercent).toFixed(2)}%
                      </div>
                    )}
                    {c.unit && <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>per {c.unit}</div>}
                  </div>
                );
              })}
              {commodities.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', padding: '1rem' }}>
                  {language === 'hi' ? 'कोई कमोडिटी डेटा नहीं' : 'No commodity data available'}
                </p>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );

  return (
    <Layout userName={userName} onLogout={onLogout} onNavigate={handleNavigate} activePage={currentSection}>
      {renderContent()}
    </Layout>
  );
}

