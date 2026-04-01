import React, { useState, useEffect } from 'react';
import Icons from '../ui/Icons';

const DialogueBox = ({ speaker, text, onContinue, isComplete, language = 'en' }) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);
    const [canSkip, setCanSkip] = useState(false);
    const isHindi = language === 'hi';
    const continueText = isHindi ? 'जारी रखने के लिए क्लिक करें →' : 'Click to continue →';
    const skipText = isHindi ? 'स्किप करें ' : 'Click to skip ';
    const completeText = isHindi ? <span style={{display:'flex',alignItems:'center',gap:'0.25rem'}}><Icons.Check size={14} /> पूर्ण</span> : <span style={{display:'flex',alignItems:'center',gap:'0.25rem'}}><Icons.Check size={14} /> Complete</span>;

    useEffect(() => {
        setDisplayedText('');
        setIsTyping(true);
        setCanSkip(false);
        let idx = 0;
        const skipTimer = setTimeout(() => setCanSkip(true), 500);
        const interval = setInterval(() => {
            if (idx < text.length) {
                setDisplayedText(text.substring(0, idx + 1));
                idx++;
            } else {
                setIsTyping(false);
                clearInterval(interval);
            }
        }, 30);
        return () => { clearInterval(interval); clearTimeout(skipTimer); };
    }, [text]);

    const handleClick = () => {
        if (isTyping && canSkip) { setDisplayedText(text); setIsTyping(false); }
        else if (!isTyping) { onContinue(); }
    };

    return (
        <div className="game-dialogue-box-container" onClick={handleClick}>
            <div className="game-dialogue-box">
                <div className="game-dialogue-speaker">{speaker?.name || 'Unknown'}</div>
                <div className="game-dialogue-text">
                    {displayedText}
                    {isTyping && <span className="game-typing-cursor">▊</span>}
                </div>
                <div className="game-dialogue-continue">
                    {!isTyping && <span className="game-continue-indicator">{isComplete ? completeText : continueText}</span>}
                    {isTyping && canSkip && <span className="game-skip-indicator">{skipText}</span>}
                </div>
            </div>
        </div>
    );
};

export default DialogueBox;
