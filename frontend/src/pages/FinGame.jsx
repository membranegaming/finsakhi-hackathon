import { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { useGameState } from '../store/useGameState';
import Icons from '../components/ui/Icons';
import DialogueScene from '../components/game/DialogueScene';
import ChoiceButton from '../components/game/ChoiceButton';
import SceneBackground from '../components/game/SceneBackground';
import GameStatsBar from '../components/game/GameStatsBar';
import StoryEndScreen from '../components/game/StoryEndScreen';
import FeedbackScreen from '../components/game/FeedbackScreen';
import '../components/game/FinGame.css';

export default function FinGame({ userId, onNavigate }) {
    const { language } = useApp();
    const langKey = language === 'hi' ? 'hindi' : 'english';
    const { state, loading: hookLoading, startGame, loadCurrentState, makeChoice, rollback } = useGameState(userId, langKey);

    // View state machine: 'paths' | 'playing' | 'ended'
    const [view, setView] = useState('paths');
    const [paths, setPaths] = useState([]);
    const [node, setNode] = useState(null);
    const [showingDialogue, setShowingDialogue] = useState(true);
    const [animating, setAnimating] = useState(false);
    const [storyEnded, setStoryEnded] = useState(false);
    const [endingData, setEndingData] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [loadingPaths, setLoadingPaths] = useState(true);

    const translations = {
        english: {
            title: 'Choose Your Financial Journey',
            subtitle: 'Select a path to begin your story',
            loading: 'Loading...',
            selectMe: 'Select Me',
            clickToSelect: 'Click to Select →',
            whatWillYouDo: 'What will you do?',
            undoLastChoice: '↶ Undo Last Choice',
            loadingStory: 'Loading your story...',
            cost: 'Cost',
        },
        hindi: {
            title: 'अपनी वित्तीय यात्रा चुनें',
            subtitle: 'अपनी कहानी शुरू करने के लिए एक रास्ता चुनें',
            loading: 'लोड हो रहा है...',
            selectMe: 'मुझे चुनें',
            clickToSelect: 'चुनने के लिए क्लिक करें →',
            whatWillYouDo: 'आप क्या करेंगे?',
            undoLastChoice: '↶ पिछला विकल्प पूर्ववत करें',
            loadingStory: 'आपकी कहानी लोड हो रही है...',
            cost: 'लागत',
        }
    };
    const t = translations[langKey];

    const pathIcons = { farming: 'FAR', business: 'BIZ', wage: 'WRK' };
    const pathColors = { farming: '#4CAF50', business: '#FF9800', wage: '#2196F3' };

    // Load paths on mount
    useEffect(() => {
        import('../services/api').then(({ default: api }) => {
            api.game.getPaths(langKey).then(data => {
                setPaths(data || []);
                setLoadingPaths(false);
            }).catch(() => setLoadingPaths(false));
        });
    }, [langKey]);

    // If user already has a game session, resume it
    useEffect(() => {
        if (state.currentPath && view === 'paths') {
            loadCurrentState().then(response => {
                if (response && response.node) {
                    setNode(response.node);
                    setShowingDialogue(response.node.dialogue?.length > 0);
                    setView('playing');
                }
            }).catch(() => {});
        }
    }, [state.currentPath]);

    const handleSelectPath = async (pathId) => {
        setAnimating(true);
        try {
            await startGame(pathId);
            const response = await loadCurrentState();
            if (response && response.node) {
                setNode(response.node);
                setShowingDialogue(response.node.dialogue?.length > 0);
                setView('playing');
            }
        } catch (e) {
            console.error('Error starting game:', e);
        }
        setAnimating(false);
    };

    const isEndingNode = (n) => {
        if (!n || !n.id) return false;
        return n.id.includes('_end_') || n.id.includes('end_');
    };

    const extractEndingData = (n) => {
        const narrative = n.text || n.narrative || '';
        const pathName = state.currentPath === 'farming' ? 'Farming / Family Income'
            : state.currentPath === 'business' ? 'Small Business / Self Employment'
            : 'Daily Wage / Job';

        const epilogueParts = narrative.split(' Key Lessons Learned:');
        const epilogue = epilogueParts[0].replace(/ Final Stats:.*$/s, '').trim();
        const lessonsMatch = narrative.match(/^\-\s+[^\n]+/gm);
        const lessonsLearned = lessonsMatch ? lessonsMatch.map(l => l.replace(/^\-\s+/, '').trim()) : [];
        const isGoodEnding = n.id.includes('good') || n.id.includes('success') || n.id.includes('growth');

        return { pathName, finalStats: state.stats, epilogue, lessonsLearned, isGoodEnding };
    };

    const handleDialogueComplete = () => {
        if (isEndingNode(node)) {
            const ending = extractEndingData(node);
            setEndingData(ending);
            setStoryEnded(true);
            setView('ended');
            return;
        }
        setShowingDialogue(false);
    };

    const handleChoice = async (choice) => {
        setAnimating(true);
        try {
            const response = await makeChoice(choice);
            // Show feedback from the choice object (not the API response)
            if (choice.feedback) {
                const adviceText = choice.feedback.advice?.[langKey] || choice.feedback.advice?.english || choice.feedback.advice || '';
                const nextScenarioText = choice.feedback.nextScenario?.[langKey] || choice.feedback.nextScenario?.english || '';
                setFeedback({
                    isCorrect: choice.feedback.isCorrect,
                    advice: adviceText,
                    nextScenarioName: nextScenarioText,
                    nextNode: response?.node || null
                });
            } else if (response && response.node) {
                setNode(response.node);
                setShowingDialogue(response.node.dialogue?.length > 0);
            }
        } catch (e) {
            console.error('Error making choice:', e);
        }
        setAnimating(false);
    };

    const handleFeedbackContinue = () => {
        if (feedback?.nextNode) {
            setNode(feedback.nextNode);
            setShowingDialogue(feedback.nextNode.dialogue?.length > 0);
        }
        setFeedback(null);
    };

    const handleRollback = async () => {
        setAnimating(true);
        try {
            await rollback();
            // rollback() already calls loadCurrentState() internally,
            // but we need the response to update the local node state
            const response = await loadCurrentState();
            if (response && response.node) {
                setNode(response.node);
                setShowingDialogue(response.node.dialogue?.length > 0);
            }
        } catch (e) {
            console.error('Rollback error:', e);
        }
        setAnimating(false);
    };

    const handleTryAnother = () => {
        setNode(null);
        setStoryEnded(false);
        setEndingData(null);
        setFeedback(null);
        setShowingDialogue(true);
        setView('paths');
    };

    const handleExit = () => {
        if (onNavigate) onNavigate('dashboard');
    };

    // --- FEEDBACK OVERLAY ---
    if (feedback) {
        return (
            <FeedbackScreen
                isCorrect={feedback.isCorrect}
                advice={feedback.advice}
                nextScenarioName={feedback.nextScenarioName}
                onContinue={handleFeedbackContinue}
                language={language}
            />
        );
    }

    // --- PATH SELECTION VIEW ---
    if (view === 'paths') {
        if (loadingPaths) return <div className="game-loading-screen">{t.loading}</div>;
        return (
            <div className="game-path-selection-page">
                <div className="game-path-header">
                    <h1 className="game-path-title">{t.title}</h1>
                    <p className="game-path-subtitle">{t.subtitle}</p>
                </div>
                <div className="game-path-boxes-container">
                    {paths.map(path => (
                        <div
                            key={path.path_id}
                            className="game-path-box"
                            onClick={() => !animating && handleSelectPath(path.path_id)}
                            style={{ '--path-color': pathColors[path.path_id] || '#6c63ff' }}
                        >
                            <div className="game-path-box-content">
                                <div className="game-path-icon" style={{ width: '64px', height: '64px', borderRadius: '50%', background: pathColors[path.path_id] || '#6c63ff', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' }}>
                                    {path.path_id === 'farming' ?
                                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg> :
                                     path.path_id === 'business' ?
                                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg> :
                                     path.path_id === 'wage' ?
                                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg> :
                                      <Icons.Target size={32} color="#fff" />}
                                </div>
                                <h2 className="game-path-name">{path.title}</h2>
                                <p className="game-path-description">{path.description}</p>
                            </div>
                            <div className="game-path-select-strip">
                                <span className="game-select-text">{t.selectMe}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // --- STORY END VIEW ---
    if (view === 'ended' && endingData) {
        return (
            <StoryEndScreen
                {...endingData}
                onTryAnother={handleTryAnother}
                onExit={handleExit}
                language={language}
            />
        );
    }

    // --- STORY PLAY VIEW ---
    if (!node) return <div className="game-loading-screen">{t.loadingStory}</div>;

    // Visual Novel: Dialogue phase
    if (node.dialogue && showingDialogue) {
        return (
            <div className="game-play-container">
                <DialogueScene
                    scene={node.scene || 'default'}
                    dialogue={node.dialogue}
                    characters={node.characters || []}
                    onDialogueComplete={handleDialogueComplete}
                    stats={state.stats}
                    language={language}
                />
            </div>
        );
    }

    // Choice phase
    return (
        <div className="game-visual-novel-container">
            <GameStatsBar stats={state.stats} language={language} />
            <SceneBackground scene={node.scene || 'default'} />
            <div className="game-choice-overlay">
                <div className="game-choice-panel">
                    <h2 className="game-choice-title">{t.whatWillYouDo}</h2>
                    <div className="game-choice-list">
                        {node.choices && node.choices.map(choice => {
                            const isPathSelection = choice.text?.includes('Different Path') ||
                                choice.text?.includes('Different Life') ||
                                choice.text?.includes('Other Life Paths');
                            return (
                                <ChoiceButton
                                    key={choice.id}
                                    onClick={() => {
                                        if (isPathSelection) handleTryAnother();
                                        else handleChoice(choice);
                                    }}
                                    disabled={animating}
                                    variant={choice.cost ? 'risky' : 'default'}
                                    subtext={choice.cost ? `${t.cost}: ₹${choice.cost}` : null}
                                >
                                    {choice.text}
                                </ChoiceButton>
                            );
                        })}
                    </div>
                    <button className="game-rollback-button" onClick={handleRollback} disabled={animating}>
                        {t.undoLastChoice}
                    </button>
                </div>
            </div>
        </div>
    );
}
