import { useState, useEffect } from "react";
import { useApp } from "../contexts/AppContext";
import { assessmentAPI } from "../services/api";
import LanguageToggle from "../components/ui/LanguageToggle";
import ThemeToggle from "../components/ui/ThemeToggle";
import "./Assessment.css";
import CandleLoader from "../components/ui/CandleLoader";

const TOTAL_PROFILE_STEPS = 6;
const TOTAL_MCQ = 8;
const TOTAL_STEPS = TOTAL_PROFILE_STEPS + TOTAL_MCQ;

export default function Assessment({ onComplete, userId }) {
  const { language } = useApp();

  // Flow state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(null);

  // Current question display
  const [phase, setPhase] = useState("profile"); // "profile" | "mcq" | "completed"
  const [question, setQuestion] = useState("");
  const [questionType, setQuestionType] = useState("text"); // "text" | "mcq"
  const [options, setOptions] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [mcqNumber, setMcqNumber] = useState(0);

  // MCQ feedback
  const [feedback, setFeedback] = useState(null); // { isCorrect, correctIdx }
  const [score, setScore] = useState(0);

  // Text input for profile text fields
  const [textAnswer, setTextAnswer] = useState("");

  // Result
  const [result, setResult] = useState(null);

  // Start assessment on mount
  useEffect(() => {
    startAssessment();
  }, []);

  const startAssessment = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await assessmentAPI.start(userId, language);
      setSessionId(res.session_id);
      setPhase(res.phase);
      setQuestion(res.question);
      setQuestionType(res.type || "text");
      setOptions(res.options || []);
      setCurrentStep(res.step || 0);
    } catch (err) {
      setError(err.message || "Failed to start assessment");
    } finally {
      setLoading(false);
    }
  };

  const handleProfileAnswer = async (answer) => {
    setLoading(true);
    setError("");
    setTextAnswer("");
    try {
      const res = await assessmentAPI.answerProfile(sessionId, String(answer));
      setSessionId(res.session_id);
      if (res.phase === "mcq") {
        // Profile done, switching to MCQ
        setPhase("mcq");
        setQuestion(res.question);
        setOptions(res.options || []);
        setMcqNumber(res.mcq_question_number || 1);
        setQuestionType("mcq");
      } else {
        // Next profile step
        setPhase("profile");
        setQuestion(res.question);
        setQuestionType(res.type || "text");
        setOptions(res.options || []);
        setCurrentStep(res.step);
      }
    } catch (err) {
      setError(err.message || "Failed to submit answer");
    } finally {
      setLoading(false);
    }
  };

  const handleMCQAnswer = async (selectedIdx) => {
    // Show feedback briefly, then submit
    setLoading(true);
    setError("");
    try {
      const res = await assessmentAPI.answerMCQ(sessionId, selectedIdx);

      if (res.phase === "completed") {
        setPhase("completed");
        setResult(res);
        setScore(res.total_score);
        return;
      }

      // Show feedback
      setFeedback({ isCorrect: res.is_correct, correctIdx: res.correct_answer_index });
      setScore(res.score_so_far || 0);

      // After a brief delay, show next question
      setTimeout(() => {
        setFeedback(null);
        setQuestion(res.question);
        setOptions(res.options || []);
        setMcqNumber(res.mcq_question_number || mcqNumber + 1);
        setLoading(false);
      }, 1500);
      return; // Don't setLoading(false) here, the timeout handles it
    } catch (err) {
      setError(err.message || "Failed to submit answer");
    }
    setLoading(false);
  };

  // Progress calculation
  const progressStep = phase === "profile" ? currentStep : TOTAL_PROFILE_STEPS + mcqNumber;
  const progress = Math.min((progressStep / TOTAL_STEPS) * 100, 100);

  // Completed view
  if (phase === "completed" && result) {
    const levelLabel = result.literacy_level === "advanced" ? "Advanced" : result.literacy_level === "intermediate" ? "Intermediate" : "Beginner";
    return (
      <div className="assessment-wrapper">
        <div className="assessment-controls-bar"><LanguageToggle /><ThemeToggle /></div>
        <div className="assessment-money-symbols">
          <span className="money-symbol">₹</span><span className="money-symbol">$</span>
          <span className="money-symbol">€</span><span className="money-symbol">£</span>
        </div>
        <div className="assessment-content">
          <div className="assessment-card" style={{ textAlign: 'center', padding: '2.5rem' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>{levelLabel}</div>
            <h2 style={{ margin: '0.5rem 0' }}>
              {language === 'hi' ? 'मूल्यांकन पूर्ण!' : 'Assessment Complete!'}
            </h2>
            <p style={{ fontSize: '1.1rem', margin: '0.5rem 0', color: 'var(--text-secondary)' }}>
              {result.message}
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', margin: '1.5rem 0', flexWrap: 'wrap' }}>
              <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem 1.5rem' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{result.total_score}/{result.total_questions}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'स्कोर' : 'Score'}</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem 1.5rem' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{result.percentage}%</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Percentage</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem 1.5rem' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--accent-primary)', textTransform: 'capitalize' }}>{result.literacy_level}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{language === 'hi' ? 'स्तर' : 'Level'}</div>
              </div>
              {result.xp_earned && (
                <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem 1.5rem' }}>
                  <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#f39c12' }}>+{result.xp_earned}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>XP Earned</div>
                </div>
              )}
            </div>

            {/* Category breakdown */}
            {result.category_breakdown && (
              <div style={{ margin: '1.5rem 0', textAlign: 'left' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>
                  {language === 'hi' ? 'श्रेणी विश्लेषण' : 'Category Breakdown'}
                </h3>
                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  {Object.entries(result.category_breakdown).map(([cat, data]) => (
                    <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '0.85rem', textTransform: 'capitalize', minWidth: '120px' }}>{cat.replace(/_/g, ' ')}</span>
                      <div style={{ flex: 1, height: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${(data.correct / data.total) * 100}%`, height: '100%', background: data.correct === data.total ? '#2ecc71' : data.correct > 0 ? '#f39c12' : '#e74c3c', borderRadius: '4px', transition: 'width 0.5s' }} />
                      </div>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{data.correct}/{data.total}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              className="primary-btn"
              style={{ marginTop: '1rem', maxWidth: '300px', margin: '1rem auto 0' }}
              onClick={() => onComplete(result.literacy_level)}
            >
              {language === 'hi' ? 'सीखना शुरू करें' : 'Start Learning'}  →
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-wrapper">
      <div className="assessment-controls-bar"><LanguageToggle /><ThemeToggle /></div>
      <div className="assessment-money-symbols">
        <span className="money-symbol">₹</span><span className="money-symbol">$</span>
        <span className="money-symbol">€</span><span className="money-symbol">£</span>
        <span className="money-symbol">¥</span><span className="money-symbol">₹</span>
      </div>

      <div className="assessment-content">
        <div className="assessment-header">
          <h1>{language === 'hi' ? 'वित्तीय साक्षरता मूल्यांकन' : 'Financial Literacy Assessment'}</h1>
          <p>
            {phase === "profile"
              ? (language === 'hi' ? 'पहले अपने बारे में बताएं' : 'Tell us about yourself first')
              : (language === 'hi' ? 'अब कुछ प्रश्नों के उत्तर दें' : 'Now answer some questions')}
          </p>
        </div>

        <div className="assessment-card">
          {/* Step indicator */}
          <div className="step-indicator">
            <div className="step-indicator-header">
              <span className="step-label">
                {language === 'hi' ? `चरण ${progressStep + 1}` : `Step ${progressStep + 1}`}
                <span className="step-total"> / {TOTAL_STEPS}</span>
              </span>
              {phase === "mcq" && (
                <span className="step-score">
                  {language === 'hi' ? 'स्कोर' : 'Score'}: {score}
                </span>
              )}
            </div>
            <div className="step-progress-track">
              <div className="step-progress-fill" style={{ width: `${progress}%` }} />
              {/* Step dots */}
              <div className="step-dots">
                {Array.from({ length: TOTAL_STEPS }, (_, i) => (
                  <div
                    key={i}
                    className={`step-dot${i < progressStep ? ' completed' : i === progressStep ? ' active' : ''}`}
                    title={`${language === 'hi' ? 'चरण' : 'Step'} ${i + 1}`}
                  />
                ))}
              </div>
            </div>
            <div className="step-phase-label">
              {phase === "profile"
                ? (language === 'hi' ? ` प्रोफ़ाइल (${currentStep + 1}/${TOTAL_PROFILE_STEPS})` : ` Profile (${currentStep + 1}/${TOTAL_PROFILE_STEPS})`)
                : (language === 'hi' ? ` प्रश्न (${mcqNumber}/${TOTAL_MCQ})` : ` Quiz (${mcqNumber}/${TOTAL_MCQ})`)}
            </div>
          </div>

          {error && (
            <p style={{ color: '#e74c3c', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</p>
          )}

          {/* Question section */}
          <div className="question-section">
            <h2>{question}</h2>

            {/* MCQ Feedback overlay */}
            {feedback && (
              <div style={{
                padding: '0.75rem 1.25rem', borderRadius: '10px', marginBottom: '1rem',
                background: feedback.isCorrect ? 'rgba(46,204,113,0.15)' : 'rgba(231,76,60,0.15)',
                border: `1px solid ${feedback.isCorrect ? '#2ecc71' : '#e74c3c'}`,
                textAlign: 'center', fontSize: '1rem'
              }}>
                {feedback.isCorrect
                  ? (language === 'hi' ? 'Correct! सही उत्तर!' : 'Correct!')
                  : (language === 'hi' ? `गलत! सही उत्तर: ${options[feedback.correctIdx]}` : `Wrong! Correct: ${options[feedback.correctIdx]}`)}
              </div>
            )}

            {/* Text input (for profile text fields like name, occupation) */}
            {phase === "profile" && questionType === "text" && !loading && (
              <form onSubmit={(e) => { e.preventDefault(); if (textAnswer.trim()) handleProfileAnswer(textAnswer); }}>
                <input
                  type="text"
                  value={textAnswer}
                  onChange={(e) => setTextAnswer(e.target.value)}
                  placeholder={language === 'hi' ? 'अपना उत्तर लिखें...' : 'Type your answer...'}
                  style={{
                    width: '100%', padding: '0.9rem 1.2rem', borderRadius: '10px',
                    border: '2px solid var(--border-color)', background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)', fontSize: '1rem', marginBottom: '1rem'
                  }}
                  autoFocus
                />
                <button type="submit" className="primary-btn" disabled={!textAnswer.trim()}>
                  {language === 'hi' ? 'आगे बढ़ें' : 'Continue'} →
                </button>
              </form>
            )}

            {/* MCQ options (for profile MCQ fields and quiz MCQs) */}
            {((phase === "profile" && questionType === "mcq") || phase === "mcq") && !loading && !feedback && (
              <div className="options-grid">
                {options.map((option, index) => (
                  <button
                    key={index}
                    className="option-btn"
                    onClick={() => {
                      if (phase === "profile") handleProfileAnswer(String(index));
                      else handleMCQAnswer(index);
                    }}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}

            {/* Loading indicator */}
            {loading && (
              <CandleLoader message={language === 'hi' ? 'लोड हो रहा है...' : 'Loading...'} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}