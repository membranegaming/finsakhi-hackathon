import React from 'react';

const FullCharacter = ({ character, position, emotion = 'neutral', isSpeaking = false }) => {
    if (!character) return null;

    const characterColors = {
        'raj': { skin: '#D4A574', clothes: '#8B4513', accent: '#F57F17' },
        'priya': { skin: '#C68642', clothes: '#FF6B35', accent: '#FDC830' },
        'amit': { skin: '#8D6E63', clothes: '#607D8B', accent: '#FF9800' },
        'mentor': { skin: '#BCAAA4', clothes: '#795548', accent: '#FFF8E7' },
        'friend': { skin: '#D7A86E', clothes: '#4CAF50', accent: '#8BC34A' },
        'banker': { skin: '#C19A6B', clothes: '#1976D2', accent: '#FFFFFF' },
        'moneylender': { skin: '#A0826D', clothes: '#424242', accent: '#FFD700' },
    };
    const colors = characterColors[character.id] || characterColors['raj'];

    return (
        <div className={`game-full-character game-full-character-${position} ${isSpeaking ? 'is-speaking' : ''}`} data-emotion={emotion}>
            <div className="game-character-illustration">
                <svg viewBox="0 0 300 500" className="game-character-svg">
                    <ellipse cx="150" cy="80" rx="50" ry="60" fill={colors.skin} />
                    <circle cx="135" cy="75" r="5" fill="#000" className={isSpeaking ? 'eye-blink' : ''} />
                    <circle cx="165" cy="75" r="5" fill="#000" className={isSpeaking ? 'eye-blink' : ''} />
                    {emotion === 'happy' && <path d="M 135 95 Q 150 105 165 95" stroke="#000" strokeWidth="2" fill="none" />}
                    {emotion === 'sad' && <path d="M 135 100 Q 150 90 165 100" stroke="#000" strokeWidth="2" fill="none" />}
                    {(emotion === 'neutral' || !['happy','sad'].includes(emotion)) && <line x1="135" y1="95" x2="165" y2="95" stroke="#000" strokeWidth="2" />}
                    <rect x="100" y="140" width="100" height="150" rx="20" fill={colors.clothes} />
                    <rect x="70" y="160" width="30" height="100" rx="15" fill={colors.skin} className={isSpeaking ? 'arm-wave-left' : ''} />
                    <rect x="200" y="160" width="30" height="100" rx="15" fill={colors.skin} className={isSpeaking ? 'arm-wave-right' : ''} />
                    <circle cx="85" cy="270" r="15" fill={colors.skin} />
                    <circle cx="215" cy="270" r="15" fill={colors.skin} />
                    <rect x="115" y="290" width="30" height="150" rx="15" fill={colors.accent} />
                    <rect x="155" y="290" width="30" height="150" rx="15" fill={colors.accent} />
                    <ellipse cx="130" cy="450" rx="20" ry="10" fill="#000" opacity="0.8" />
                    <ellipse cx="170" cy="450" rx="20" ry="10" fill="#000" opacity="0.8" />
                    <circle cx="150" cy="180" r="8" fill={colors.accent} />
                    <circle cx="150" cy="210" r="8" fill={colors.accent} />
                    <circle cx="150" cy="240" r="8" fill={colors.accent} />
                </svg>
            </div>
            {isSpeaking && <div className="game-speaking-indicator"><span>💭</span></div>}
        </div>
    );
};

export default FullCharacter;
