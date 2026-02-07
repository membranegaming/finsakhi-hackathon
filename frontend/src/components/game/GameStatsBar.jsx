import React from 'react';

const GameStatsBar = ({ stats, language = 'en' }) => {
    const savings = stats?.savings ?? 0;
    const debt = stats?.debt ?? 0;
    const confidence = stats?.confidence ?? 50;
    const isHindi = language === 'hi';

    const labels = {
        savings: isHindi ? 'बचत' : 'Savings',
        debt: isHindi ? 'कर्ज' : 'Debt',
        confidence: isHindi ? 'आत्मविश्वास' : 'Confidence',
    };

    const getConfidenceColor = (c) => {
        if (c >= 70) return '#4CAF50';
        if (c >= 40) return '#FF9800';
        return '#F44336';
    };

    const getDebtStatus = (d) => {
        if (d === 0) return 'debt-free';
        if (d < 3000) return 'debt-low';
        if (d < 6000) return 'debt-medium';
        return 'debt-high';
    };

    return (
        <div className="game-stats-bar">
            <div className="game-stats-container">
                <div className="game-stat-item game-stat-savings">
                    <div className="game-stat-icon">💰</div>
                    <div className="game-stat-content">
                        <div className="game-stat-label">{labels.savings}</div>
                        <div className="game-stat-value">₹{savings.toLocaleString()}</div>
                    </div>
                </div>
                <div className={`game-stat-item game-stat-debt ${getDebtStatus(debt)}`}>
                    <div className="game-stat-icon">📊</div>
                    <div className="game-stat-content">
                        <div className="game-stat-label">{labels.debt}</div>
                        <div className="game-stat-value">₹{debt.toLocaleString()}</div>
                    </div>
                </div>
                <div className="game-stat-item game-stat-confidence">
                    <div className="game-stat-icon">⭐</div>
                    <div className="game-stat-content">
                        <div className="game-stat-label">{labels.confidence}</div>
                        <div className="game-stat-value" style={{ color: getConfidenceColor(confidence) }}>
                            {confidence}%
                        </div>
                    </div>
                    <div className="game-confidence-bar">
                        <div className="game-confidence-fill" style={{ width: `${confidence}%`, backgroundColor: getConfidenceColor(confidence) }} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GameStatsBar;
