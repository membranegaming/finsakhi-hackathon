import React from 'react';

const FeedbackScreen = ({ isCorrect, advice, nextScenarioName, onContinue, language = 'en' }) => {
    const langKey = language === 'hi' ? 'hindi' : 'english';

    const translations = {
        english: {
            goodChoice: "Good Choice!",
            needsImprovement: "Think Again!",
            advice: "Advice",
            nextScenario: "Next Scenario",
            continue: "Continue"
        },
        hindi: {
            goodChoice: "अच्छा विकल्प!",
            needsImprovement: "फिर से सोचें!",
            advice: "सलाह",
            nextScenario: "अगला परिदृश्य",
            continue: "जारी रखें"
        }
    };

    const t = translations[langKey];

    return (
        <div className="game-feedback-screen">
            <div className="game-feedback-container">
                <div className={`game-feedback-icon ${isCorrect ? 'correct' : 'warning'}`}>
                    {isCorrect ? '✓' : '⚠'}
                </div>
                <h2 className={`game-feedback-title ${isCorrect ? 'correct' : 'warning'}`}>
                    {isCorrect ? t.goodChoice : t.needsImprovement}
                </h2>
                <div className="game-advice-box">
                    <h3 className="game-advice-label">{t.advice}:</h3>
                    <p className="game-advice-text">{advice}</p>
                </div>
                {nextScenarioName && (
                    <div className="game-next-scenario-info">
                        <span className="game-next-label">{t.nextScenario}:</span>
                        <span className="game-scenario-name">{nextScenarioName}</span>
                    </div>
                )}
                <button className="game-continue-button" onClick={onContinue}>
                    {t.continue} →
                </button>
            </div>
        </div>
    );
};

export default FeedbackScreen;
