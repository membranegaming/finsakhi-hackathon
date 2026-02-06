import { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../store/authStore.jsx';
import { recommendationsAPI } from '../services/api';
import './Schemes.css';
import CandleLoader from '../components/ui/CandleLoader';

export default function Schemes({ userId: propUserId }) {
  const { language } = useApp();
  const auth = useAuth();
  const userId = propUserId || auth.userId;

  const [tab, setTab] = useState('schemes'); // "schemes" | "cards"
  const [schemes, setSchemes] = useState([]);
  const [cards, setCards] = useState([]);
  const [aiSummary, setAiSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { if (userId) loadData(); }, [userId, tab, language]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      if (tab === 'schemes') {
        const res = await recommendationsAPI.getGovtSchemes(userId, language);
        setSchemes(res.schemes || []);
        setAiSummary(res.ai_summary || '');
      } else {
        const res = await recommendationsAPI.getCreditCards(userId, language);
        setCards(res.cards || []);
        setAiSummary(res.ai_summary || '');
      }
    } catch (e) {
      setError(e.message);
      // Fallback: try loading all
      try {
        if (tab === 'schemes') {
          const all = await recommendationsAPI.getAllSchemes();
          setSchemes(all.schemes || all || []);
        } else {
          const all = await recommendationsAPI.getAllCards();
          setCards(all.cards || all || []);
        }
      } catch (e2) { /* ignore */ }
    }
    setLoading(false);
  };

  return (
    <div className="schemes-page">
      <div className="schemes-header">
        <h1>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
          {language === 'hi' ? 'अनुशंसाएँ' : 'Recommendations'}
        </h1>
        <p>{language === 'hi' ? 'आपकी प्रोफ़ाइल के आधार पर व्यक्तिगत सुझाव' : 'Personalized suggestions based on your profile'}</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
        <button onClick={() => setTab('schemes')}
          className={`filter-btn ${tab === 'schemes' ? 'active' : ''}`}>
          🏛️ {language === 'hi' ? 'सरकारी योजनाएँ' : 'Govt Schemes'}
        </button>
        <button onClick={() => setTab('cards')}
          className={`filter-btn ${tab === 'cards' ? 'active' : ''}`}>
          💳 {language === 'hi' ? 'क्रेडिट कार्ड' : 'Credit Cards'}
        </button>
      </div>

      {/* AI Summary */}
      {aiSummary && (
        <div style={{ background: 'var(--card-bg)', borderRadius: '12px', padding: '1rem', marginBottom: '1.25rem', border: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>🤖 {language === 'hi' ? 'AI सारांश' : 'AI Summary'}</h3>
          <p style={{ fontSize: '0.85rem', lineHeight: 1.7, whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>{aiSummary}</p>
        </div>
      )}

      {error && <p style={{ color: '#e74c3c', marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</p>}

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'लोड हो रहा है...' : 'Loading recommendations...'} />
      ) : tab === 'schemes' ? (
        <div className="schemes-grid">
          {schemes.map((scheme, i) => (
            <div key={i} className="scheme-card eligible">
              <div className="scheme-header">
                <h3>{scheme.name_hi && language === 'hi' ? scheme.name_hi : scheme.name}</h3>
                {scheme.category && (
                  <span className="status-badge eligible" style={{ textTransform: 'capitalize' }}>{scheme.category}</span>
                )}
              </div>
              <p className="scheme-description">{scheme.description}</p>
              <div className="scheme-details">
                {scheme.eligibility && (
                  <div className="detail-section">
                    <h4>{language === 'hi' ? 'पात्रता' : 'Eligibility'}</h4>
                    <p>{scheme.eligibility}</p>
                  </div>
                )}
                {scheme.benefits && scheme.benefits.length > 0 && (
                  <div className="detail-section">
                    <h4>{language === 'hi' ? 'लाभ' : 'Benefits'}</h4>
                    <ul>{scheme.benefits.map((b, j) => <li key={j}>{b}</li>)}</ul>
                  </div>
                )}
                {scheme.how_to_apply && (
                  <div className="detail-section">
                    <h4>{language === 'hi' ? 'कैसे आवेदन करें' : 'How to Apply'}</h4>
                    <p>{scheme.how_to_apply}</p>
                  </div>
                )}
              </div>
              {scheme.apply_url && (
                <a href={scheme.apply_url} target="_blank" rel="noopener noreferrer" className="apply-btn" style={{ display: 'inline-block', textDecoration: 'none', textAlign: 'center' }}>
                  {language === 'hi' ? 'अभी आवेदन करें' : 'Apply Now'} ↗
                </a>
              )}
            </div>
          ))}
          {schemes.length === 0 && (
            <p style={{ color: 'var(--text-secondary)', gridColumn: '1 / -1', textAlign: 'center', padding: '2rem' }}>
              {language === 'hi' ? 'कोई योजना उपलब्ध नहीं' : 'No schemes available'}
            </p>
          )}
        </div>
      ) : (
        /* Credit cards */
        <div className="schemes-grid">
          {cards.map((card, i) => (
            <div key={i} className="scheme-card eligible">
              <div className="scheme-header">
                <h3>{card.name}</h3>
                <span className="status-badge eligible">{card.bank || card.card_type}</span>
              </div>
              <p className="scheme-description">{card.best_for}</p>
              <div className="scheme-details">
                <div className="detail-section">
                  <h4>{language === 'hi' ? 'वार्षिक शुल्क' : 'Annual Fee'}</h4>
                  <p>{card.annual_fee}</p>
                </div>
                {card.eligibility && (
                  <div className="detail-section">
                    <h4>{language === 'hi' ? 'पात्रता' : 'Eligibility'}</h4>
                    <p>{card.eligibility}</p>
                  </div>
                )}
                {card.benefits && card.benefits.length > 0 && (
                  <div className="detail-section">
                    <h4>{language === 'hi' ? 'लाभ' : 'Benefits'}</h4>
                    <ul>{card.benefits.map((b, j) => <li key={j}>{b}</li>)}</ul>
                  </div>
                )}
              </div>
              {card.apply_url && (
                <a href={card.apply_url} target="_blank" rel="noopener noreferrer" className="apply-btn" style={{ display: 'inline-block', textDecoration: 'none', textAlign: 'center' }}>
                  {language === 'hi' ? 'अभी आवेदन करें' : 'Apply Now'} ↗
                </a>
              )}
            </div>
          ))}
          {cards.length === 0 && (
            <p style={{ color: 'var(--text-secondary)', gridColumn: '1 / -1', textAlign: 'center', padding: '2rem' }}>
              {language === 'hi' ? 'कोई कार्ड उपलब्ध नहीं' : 'No cards available'}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

