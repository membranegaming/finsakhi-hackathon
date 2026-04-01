import { useState, useEffect, useMemo } from 'react';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../store/authStore.jsx';
import { learningAPI, assessmentAPI } from '../services/api';
import './Analytics.css';
import CandleLoader from '../components/ui/CandleLoader';

// ── Seeded PRNG for deterministic "random" data per user ──
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function generateFinancialData(userId) {
  const rng = seededRandom((userId || 1) * 7919);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  const baseIncome = 15000 + Math.floor(rng() * 25000); // ₹15k–40k

  const monthly = months.map((m) => {
    const income = baseIncome + Math.floor(rng() * 5000 - 2000);
    const expenseRatio = 0.55 + rng() * 0.3; // 55–85% of income
    const expense = Math.floor(income * expenseRatio);
    return { month: m, income, expense, savings: income - expense };
  });

  const categoryNames = [
    { en: 'Groceries', hi: 'किराना', icon: 'GRC' },
    { en: 'Rent', hi: 'किराया', icon: 'RNT' },
    { en: 'Transport', hi: 'यातायात', icon: 'TRP' },
    { en: 'Health', hi: 'स्वास्थ्य', icon: 'HLT' },
    { en: 'Education', hi: 'शिक्षा', icon: 'EDU' },
    { en: 'Entertainment', hi: 'मनोरंजन', icon: 'ENT' },
  ];
  const colors = ['#FF8C00', '#FFA500', '#8B4513', '#D4A574', '#E67E00', '#A0522D'];
  const totalExpense = monthly.reduce((s, m) => s + m.expense, 0);
  let remaining = 100;
  const categories = categoryNames.map((cat, i) => {
    const pct = i === categoryNames.length - 1 ? remaining : Math.floor(5 + rng() * 25);
    remaining -= pct;
    if (remaining < 0) remaining = 0;
    return {
      ...cat,
      amount: Math.floor(totalExpense * pct / 100),
      percentage: pct,
      color: colors[i],
    };
  });

  return { monthly, categories, totalIncome: monthly.reduce((s, m) => s + m.income, 0), totalExpense };
}

export default function Analytics({ userId: propUserId }) {
  const { language } = useApp();
  const auth = useAuth();
  const userId = propUserId || auth.userId;

  const [healthData, setHealthData] = useState(null);
  const [assessmentHistory, setAssessmentHistory] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);

  const finData = useMemo(() => generateFinancialData(userId), [userId]);

  useEffect(() => {
    if (userId) loadAnalytics();
  }, [userId]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [healthRes, historyRes, progressRes] = await Promise.allSettled([
        learningAPI.getHealth(userId),
        assessmentAPI.getHistory(userId),
        learningAPI.getProgress(userId),
      ]);
      if (healthRes.status === 'fulfilled') setHealthData(healthRes.value);
      if (historyRes.status === 'fulfilled') setAssessmentHistory(historyRes.value?.assessments || []);
      if (progressRes.status === 'fulfilled') setProgress(progressRes.value?.progress || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const healthScore = healthData?.health_score ?? 0;
  const currentLevel = healthData?.current_level || auth.userLevel || 'beginner';
  const completedLessons = progress.filter(p => p.completed).length;
  const totalLessons = progress.length;
  const scenariosCorrect = progress.filter(p => p.scenario_correct).length;
  const maxBar = Math.max(...finData.monthly.map(m => Math.max(m.income, m.expense)), 1);

  const fmt = (v) => `₹${v.toLocaleString('en-IN')}`;

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
          {language === 'hi' ? 'वित्तीय विश्लेषण' : 'Financial Analytics'}
        </h1>
        <p>{language === 'hi' ? 'अपनी प्रगति और वित्तीय स्वास्थ्य ट्रैक करें' : 'Track your progress and financial health'}</p>
      </div>

      {loading ? (
        <CandleLoader message={language === 'hi' ? 'लोड हो रहा है...' : 'Loading analytics...'} />
      ) : (
        <div className="analytics-grid">
          {/* ─── Income vs Expense Bar Chart ─── */}
          <div className="analytics-card chart-card">
            <h3>{language === 'hi' ? 'आय बनाम खर्च (6 महीने)' : 'Income vs Expense (6 Months)'}</h3>
            <div className="bar-chart">
              {finData.monthly.map((m, i) => (
                <div className="chart-column" key={i}>
                  <div className="bars">
                    <div className="bar income-bar" style={{ height: `${(m.income / maxBar) * 170}px` }}>
                      <div className="bar-tooltip">{fmt(m.income)}</div>
                    </div>
                    <div className="bar expense-bar" style={{ height: `${(m.expense / maxBar) * 170}px` }}>
                      <div className="bar-tooltip">{fmt(m.expense)}</div>
                    </div>
                  </div>
                  <span className="chart-label">{m.month}</span>
                </div>
              ))}
            </div>
            <div className="chart-legend">
              <div className="legend-item"><span className="dot income"></span>{language === 'hi' ? 'आय' : 'Income'}</div>
              <div className="legend-item"><span className="dot expense"></span>{language === 'hi' ? 'खर्च' : 'Expense'}</div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '1rem', fontSize: '0.85rem' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: 'var(--text-secondary)' }}>{language === 'hi' ? 'कुल आय' : 'Total Income'}</div>
                <strong style={{ color: '#FF8C00' }}>{fmt(finData.totalIncome)}</strong>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: 'var(--text-secondary)' }}>{language === 'hi' ? 'कुल खर्च' : 'Total Expense'}</div>
                <strong style={{ color: '#8B4513' }}>{fmt(finData.totalExpense)}</strong>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: 'var(--text-secondary)' }}>{language === 'hi' ? 'बचत' : 'Savings'}</div>
                <strong style={{ color: '#2ecc71' }}>{fmt(finData.totalIncome - finData.totalExpense)}</strong>
              </div>
            </div>
          </div>

          {/* ─── Category Spending ─── */}
          <div className="analytics-card chart-card">
            <h3>{language === 'hi' ? 'श्रेणी-वार खर्च' : 'Spending by Category'}</h3>
            <div className="category-list">
              {finData.categories.map((cat, i) => (
                <div className="category-item" key={i}>
                  <div className="category-info">
                    <span className="category-name">
                    <span style={{ fontSize: '0.6rem', fontWeight: 700, background: cat.color, color: '#fff', padding: '1px 4px', borderRadius: '3px', letterSpacing: '0.03em', marginRight: '0.35rem' }}>{cat.icon}</span>
                    {language === 'hi' ? cat.hi : cat.en}
                  </span>
                    <span className="category-amount">{fmt(cat.amount)}</span>
                  </div>
                  <div className="category-bar-wrapper">
                    <div className="category-bar" style={{ width: `${cat.percentage}%`, background: cat.color }}></div>
                  </div>
                  <span className="category-percentage">{cat.percentage}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* ─── Financial Health Score ─── */}
          <div className="analytics-card health-score-card">
            <h3>{language === 'hi' ? 'वित्तीय स्वास्थ्य स्कोर' : 'Financial Health Score'}</h3>
            <div className="health-score-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="var(--border-subtle)" strokeWidth="8" />
                <circle cx="50" cy="50" r="45" fill="none" stroke="var(--accent-primary)" strokeWidth="8"
                  strokeDasharray={`${healthScore * 2.83} 283`} strokeLinecap="round" transform="rotate(-90 50 50)" />
              </svg>
              <span className="score-value">{healthScore}</span>
            </div>
            <div className="health-metrics">
              <div className="metric">
                <span>{language === 'hi' ? 'स्तर' : 'Level'}</span>
                <strong style={{ textTransform: 'capitalize' }}>{currentLevel}</strong>
              </div>
              <div className="metric">
                <span>{language === 'hi' ? 'पाठ पूरे' : 'Lessons Done'}</span>
                <strong>{completedLessons}/{totalLessons}</strong>
              </div>
              <div className="metric">
                <span>{language === 'hi' ? 'परिदृश्य सही' : 'Scenarios Correct'}</span>
                <strong>{scenariosCorrect}</strong>
              </div>
              {healthData?.revision_mode && (
                <div className="metric">
                  <span style={{ color: '#e74c3c' }}>{language === 'hi' ? 'रिवीजन मोड' : 'Revision Mode'}</span>
                  <strong style={{ color: '#e74c3c' }}>Active</strong>
                </div>
              )}
            </div>
          </div>

          {/* ─── Assessment History ─── */}
          <div className="analytics-card">
            <h3>{language === 'hi' ? 'मूल्यांकन इतिहास' : 'Assessment History'}</h3>
            {assessmentHistory.length > 0 ? (
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {assessmentHistory.map((a, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                    <div>
                      <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{a.literacy_level}</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginLeft: '0.5rem' }}>
                        {a.completed_at ? new Date(a.completed_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                    <span style={{ fontWeight: 'bold', color: 'var(--accent-primary)' }}>{a.total_score}/8</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', padding: '1rem 0' }}>
                {language === 'hi' ? 'कोई मूल्यांकन नहीं हुआ' : 'No assessments completed yet'}
              </p>
            )}
          </div>

          {/* ─── Learning Progress ─── */}
          <div className="analytics-card">
            <h3>{language === 'hi' ? 'सीखने की प्रगति' : 'Learning Progress'}</h3>
            {progress.length > 0 ? (
              <div style={{ display: 'grid', gap: '0.4rem' }}>
                {progress.map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0' }}>
                    <span style={{ color: p.completed ? '#2ecc71' : 'var(--text-secondary)' }}>{p.completed ? '[OK]' : '[ ]'}</span>
                    <span style={{ flex: 1, fontSize: '0.85rem' }}>{p.lesson_title || `Lesson ${p.lesson_id}`}</span>
                    {p.scenario_correct !== null && (
                      <span style={{ fontSize: '0.75rem', color: p.scenario_correct ? '#2ecc71' : '#e74c3c' }}>
                      {p.scenario_correct ? '✓' : '✗'}
                      </span>
                    )}
                    {p.xp_earned > 0 && (
                      <span style={{ fontSize: '0.7rem', color: '#f39c12' }}>+{p.xp_earned}xp</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', padding: '1rem 0' }}>
                {language === 'hi' ? 'अभी तक कोई प्रगति नहीं' : 'No learning progress yet'}
              </p>
            )}
          </div>

          {/* ─── Quick Stats ─── */}
          <div className="analytics-card stats-card">
            <h3>{language === 'hi' ? 'त्वरित आँकड़े' : 'Quick Stats'}</h3>
            <div className="quick-stats">
              <div className="stat-box">
                <span className="stat-label">{language === 'hi' ? 'स्वास्थ्य स्कोर' : 'Health Score'}</span>
                <span className="stat-value">{healthScore}/100</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">{language === 'hi' ? 'पाठ पूरे' : 'Lessons Completed'}</span>
                <span className="stat-value">{completedLessons}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">{language === 'hi' ? 'मासिक बचत दर' : 'Monthly Savings Rate'}</span>
                <span className="stat-value positive">
                  {Math.round(((finData.totalIncome - finData.totalExpense) / finData.totalIncome) * 100)}%
                </span>
              </div>
              <div className="stat-box">
                <span className="stat-label">{language === 'hi' ? 'मूल्यांकन' : 'Assessments'}</span>
                <span className="stat-value">{assessmentHistory.length}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

