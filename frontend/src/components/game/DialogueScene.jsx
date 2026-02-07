import React, { useState, useEffect } from 'react';
import AnimatedBackground from './AnimatedBackground';
import FullCharacter from './FullCharacter';
import DialogueBox from './DialogueBox';
import GameStatsBar from './GameStatsBar';

const DialogueScene = ({ scene, dialogue, characters, onDialogueComplete, stats, language = 'en' }) => {
    const [currentDialogueIndex, setCurrentDialogueIndex] = useState(0);
    const [showingDialogue, setShowingDialogue] = useState(true);

    useEffect(() => {
        setCurrentDialogueIndex(0);
        setShowingDialogue(true);
    }, [dialogue]);

    const handleContinue = () => {
        if (currentDialogueIndex < dialogue.length - 1) {
            setCurrentDialogueIndex(currentDialogueIndex + 1);
        } else {
            setShowingDialogue(false);
            onDialogueComplete();
        }
    };

    if (!dialogue || dialogue.length === 0) return null;

    const currentDialogue = dialogue[currentDialogueIndex];
    const isLastDialogue = currentDialogueIndex === dialogue.length - 1;
    const leftCharacter = dialogue.find(d => d.position === 'left');
    const rightCharacter = dialogue.find(d => d.position === 'right');
    const leftChar = leftCharacter ? characters.find(c => c.id === leftCharacter.speaker) : null;
    const rightChar = rightCharacter ? characters.find(c => c.id === rightCharacter.speaker) : null;
    const currentSpeaker = characters.find(c => c.id === currentDialogue.speaker);
    const isSpeakingLeft = currentDialogue.position === 'left';
    const isSpeakingRight = currentDialogue.position === 'right';

    return (
        <div className="game-dialogue-scene">
            <GameStatsBar stats={stats} language={language} />
            <AnimatedBackground scene={scene} />
            {leftChar && <FullCharacter character={leftChar} position="left" emotion={isSpeakingLeft ? currentDialogue.emotion : 'neutral'} isSpeaking={isSpeakingLeft} />}
            {rightChar && <FullCharacter character={rightChar} position="right" emotion={isSpeakingRight ? currentDialogue.emotion : 'neutral'} isSpeaking={isSpeakingRight} />}
            {showingDialogue && (
                <DialogueBox speaker={currentSpeaker} text={currentDialogue.text} onContinue={handleContinue} isComplete={isLastDialogue} language={language} />
            )}
            <div className="game-dialogue-progress">
                {dialogue.map((_, index) => (
                    <div key={index} className={`game-progress-dot ${index === currentDialogueIndex ? 'active' : ''} ${index < currentDialogueIndex ? 'completed' : ''}`} />
                ))}
            </div>
        </div>
    );
};

export default DialogueScene;
