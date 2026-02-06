import { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import LanguageToggle from '../components/ui/LanguageToggle';
import ThemeToggle from '../components/ui/ThemeToggle';
import './PersonalDetails.css';
import CandleLoader from '../components/ui/CandleLoader';

function PersonalDetails({ onComplete, userName = "Guest", onCancel, isEditing = false }) {
  const { t } = useApp();
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  useEffect(() => {
    // Use sample data directly (until backend is connected)
    // Number of questions will be fetched from backend once integrated
    setQuestions([
      { id: 0, question: 'What is your full name?', type: 'text', required: true },
      { id: 1, question: 'What is your age?', type: 'number', required: true },
      { id: 2, question: 'What is your annual income range?', type: 'select', required: true, options: ['0-3 Lakhs', '3-6 Lakhs', '6-10 Lakhs', '10+ Lakhs'] }
    ]);
    setLoading(false);
  }, []);

  const handleInputChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const currentQuestion = questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const isFirstQuestion = currentQuestionIndex === 0;

  const isCurrentAnswerValid = () => {
    if (!currentQuestion) return false;
    const answer = answers[currentQuestion.id];
    return answer && answer.toString().trim() !== '';
  };

  const handleNext = () => {
    if (isCurrentAnswerValid() && !isLastQuestion) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (!isFirstQuestion) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isCurrentAnswerValid()) return;

    setSubmitting(true);

    // Simulate brief delay (until backend is connected)
    await new Promise(resolve => setTimeout(resolve, 500));

    // Pass the user's name to the parent component
    // Priority: 1. Name from form, 2. Name from login/signup, 3. Default 'User'
    const finalUserName = answers[0] || userName || 'User';
    onComplete(finalUserName);

    setSubmitting(false);
  };

  const renderQuestion = (question) => {
    switch (question.type) {
      case 'text':
      case 'number':
        return (
          <div className="answer-section">
            <label className="answer-label">Your Answer</label>
            <input
              type={question.type}
              value={answers[question.id] || ''}
              onChange={(e) => handleInputChange(question.id, e.target.value)}
              required={question.required}
              className="form-input"
              placeholder={question.type === 'text' ? 'Type your answer here...' : 'Enter a number...'}
            />
          </div>
        );

      case 'select':
        return (
          <div className="answer-section">
            <label className="answer-label">Your Answer</label>
            <select
              value={answers[question.id] || ''}
              onChange={(e) => handleInputChange(question.id, e.target.value)}
              required={question.required}
              className="form-select"
            >
              <option value="">Select an option</option>
              {question.options?.map((option, index) => (
                <option key={index} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="personal-details-wrapper">
      {/* Controls bar - top right */}
      <div className="pd-controls-bar">
        {onCancel && (
          <button className="back-to-dashboard-btn" onClick={onCancel}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Back to Dashboard
          </button>
        )}
        <LanguageToggle />
        <ThemeToggle />
      </div>

      {/* Floating money symbols background */}
      <div className="pd-money-symbols">
        <span className="money-symbol">₹</span>
        <span className="money-symbol">$</span>
        <span className="money-symbol">€</span>
        <span className="money-symbol">£</span>
        <span className="money-symbol">¥</span>
        <span className="money-symbol">₹</span>
        <span className="money-symbol">$</span>
        <span className="money-symbol">€</span>
      </div>

      <div className="personal-details-container">
        <div className="personal-details-header">
          <h1>{t('personalDetails.title')}</h1>
          <p className="subtitle">{t('personalDetails.subtitle')}</p>
        </div>

        <div className="personal-details-card">
          {loading ? (
            <CandleLoader message={t('personalDetails.loading')} />
          ) : (
            <form onSubmit={handleSubmit} className="details-form">
              {/* Upper half - Image section */}
              <div className="card-image-section">
                <div className="image-container">
                  {/* Decorative illustration */}
                  <svg viewBox="0 0 200 120" className="illustration-svg">
                    {/* Background shapes */}
                    <circle cx="100" cy="60" r="50" fill="#FFFFFF" opacity="0.3" />
                    <circle cx="140" cy="40" r="25" fill="#8B4513" opacity="0.2" />
                    <circle cx="60" cy="80" r="20" fill="#FFFFFF" opacity="0.2" />

                    {/* Person icon */}
                    <circle cx="100" cy="45" r="18" fill="#FFFFFF" />
                    <path d="M70 95 Q100 70 130 95" fill="#FFFFFF" />

                    {/* Document/form icon */}
                    <rect x="145" y="50" width="30" height="40" rx="3" fill="#8B4513" />
                    <line x1="152" y1="60" x2="168" y2="60" stroke="#FFFFFF" strokeWidth="2" />
                    <line x1="152" y1="70" x2="168" y2="70" stroke="#FFFFFF" strokeWidth="2" />
                    <line x1="152" y1="80" x2="162" y2="80" stroke="#FFFFFF" strokeWidth="2" />

                    {/* Checkmark */}
                    <circle cx="35" cy="50" r="15" fill="#8B4513" />
                    <polyline points="28,50 33,55 43,45" fill="none" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <p className="image-caption">Tell us about yourself</p>
              </div>

              {/* Divider */}
              <div className="card-divider"></div>

              {/* Lower half - Question section */}
              <div className="card-question-section">
                {/* Progress indicator */}
                <div className="question-progress">
                  <div className="progress-text">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Single question display */}
                {currentQuestion && (
                  <div className="form-group single-question">
                    <label className="form-label">
                      {currentQuestion.question}
                      {currentQuestion.required && <span className="required">*</span>}
                    </label>
                    {renderQuestion(currentQuestion)}
                  </div>
                )}
              </div>

              {/* Navigation buttons */}
              <div className="question-navigation">
                <button
                  type="button"
                  className={`nav-btn prev-btn ${isFirstQuestion ? 'hidden' : ''}`}
                  onClick={handlePrevious}
                  disabled={isFirstQuestion}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                  </svg>
                  Previous
                </button>

                {isLastQuestion ? (
                  <button
                    type="submit"
                    className={`primary-btn submit-btn ${!isCurrentAnswerValid() || submitting ? 'disabled' : ''}`}
                    disabled={!isCurrentAnswerValid() || submitting}
                  >
                    {submitting ? t('personalDetails.submitting') : t('common.submit')}
                  </button>
                ) : (
                  <button
                    type="button"
                    className={`primary-btn next-btn ${!isCurrentAnswerValid() ? 'disabled' : ''}`}
                    onClick={handleNext}
                    disabled={!isCurrentAnswerValid()}
                  >
                    Next
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </button>
                )}
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default PersonalDetails;

