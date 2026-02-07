import React from 'react';

const StoryEndScreen = ({ pathName, finalStats, epilogue, lessonsLearned, isGoodEnding = true, onTryAnother, onExit, language = 'en' }) => {
    const langKey = language === 'hi' ? 'hindi' : 'english';

    const translations = {
        english: {
            journeyComplete: "Journey Complete!",
            path: "Path",
            yourStory: "Your Story",
            finalStats: "Final Stats",
            savings: "Savings",
            debt: "Debt",
            confidence: "Confidence",
            lessonsLearned: "Lessons Learned",
            tryAnother: "Try Another Path",
            exit: "Back to Dashboard"
        },
        hindi: {
            journeyComplete: "यात्रा पूरी हुई!",
            path: "रास्ता",
            yourStory: "आपकी कहानी",
            finalStats: "अंतिम आँकड़े",
            savings: "बचत",
            debt: "कर्ज",
            confidence: "आत्मविश्वास",
            lessonsLearned: "सीखे गए सबक",
            tryAnother: "दूसरा रास्ता आज़माएं",
            exit: "डैशबोर्ड पर वापस"
        }
    };

    const t = translations[langKey];

    return (
        <div className="game-story-end-screen">
            <div className="game-end-screen-container">
                <div className="game-end-header">
                    <div className={`game-end-icon ${isGoodEnding ? 'success' : 'neutral'}`}>
                        {isGoodEnding ? '🎉' : '📊'}
                    </div>
                    <h1 className="game-end-title">{t.journeyComplete}</h1>
                    <h2 className="game-end-path-name">{pathName} {t.path}</h2>
                </div>

                <div className="game-end-content">
                    {epilogue && (
                        <div className="game-epilogue-section">
                            <h3 className="game-section-title">{t.yourStory}</h3>
                            <p className="game-epilogue-text">{epilogue}</p>
                        </div>
                    )}

                    <div className="game-stats-summary">
                        <h3 className="game-section-title">{t.finalStats}</h3>
                        <div className="game-stats-grid">
                            <div className="game-stat-card savings">
                                <div className="game-stat-card-icon">💰</div>
                                <div className="game-stat-card-info">
                                    <div className="game-stat-card-label">{t.savings}</div>
                                    <div className="game-stat-card-value">₹{finalStats?.savings?.toLocaleString() || 0}</div>
                                </div>
                            </div>
                            <div className="game-stat-card debt">
                                <div className="game-stat-card-icon">📊</div>
                                <div className="game-stat-card-info">
                                    <div className="game-stat-card-label">{t.debt}</div>
                                    <div className="game-stat-card-value">₹{finalStats?.debt?.toLocaleString() || 0}</div>
                                </div>
                            </div>
                            <div className="game-stat-card confidence">
                                <div className="game-stat-card-icon">⭐</div>
                                <div className="game-stat-card-info">
                                    <div className="game-stat-card-label">{t.confidence}</div>
                                    <div className="game-stat-card-value">{finalStats?.confidence || 50}%</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {lessonsLearned && lessonsLearned.length > 0 && (
                        <div className="game-lessons-section">
                            <h3 className="game-section-title">{t.lessonsLearned}</h3>
                            <ul className="game-lessons-list">
                                {lessonsLearned.map((lesson, index) => (
                                    <li key={index} className="game-lesson-item">
                                        <span className="game-lesson-icon">✓</span>
                                        {lesson}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                <div className="game-end-actions">
                    <button className="game-action-btn game-another-path-btn" onClick={onTryAnother}>
                        <span className="game-btn-icon">🌟</span>
                        <span className="game-btn-text">{t.tryAnother}</span>
                    </button>
                    <button className="game-action-btn game-exit-btn" onClick={onExit}>
                        <span className="game-btn-icon">🏠</span>
                        <span className="game-btn-text">{t.exit}</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StoryEndScreen;
