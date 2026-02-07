/**
 * useGameState — React hook for FinGame RPG state management.
 * Replaces the standalone RPG GameContext, uses FinSakhi's auth + API.
 */

import { useState, useCallback } from 'react';
import { gameAPI } from '../services/api';

export function useGameState(userId, language = 'english') {
  const [gameState, setGameState] = useState({
    stats: { savings: 0, debt: 0, confidence: 50 },
    currentPath: null,
    currentNodeId: 'start',
  });
  const [loading, setLoading] = useState(false);

  const startGame = useCallback(async (pathId) => {
    setLoading(true);
    try {
      const res = await gameAPI.setPath(userId, pathId, language);
      setGameState(prev => ({
        ...prev,
        currentPath: pathId,
        currentNodeId: res.node?.id || 'start',
        stats: res.state || prev.stats,
      }));
      return res;
    } finally {
      setLoading(false);
    }
  }, [userId, language]);

  const loadCurrentState = useCallback(async () => {
    setLoading(true);
    try {
      const res = await gameAPI.getCurrent(userId, language);
      setGameState(prev => ({
        ...prev,
        currentNodeId: res.node?.id || prev.currentNodeId,
        stats: res.state || prev.stats,
      }));
      return res;
    } finally {
      setLoading(false);
    }
  }, [userId, language]);

  const makeChoice = useCallback(async (choice) => {
    try {
      const res = await gameAPI.choose(userId, choice.id, language);
      setGameState(prev => ({
        ...prev,
        currentNodeId: res.node?.id || prev.currentNodeId,
        stats: res.state || prev.stats,
      }));
      return res;
    } catch (err) {
      console.error('FinGame choice error:', err);
      throw err;
    }
  }, [userId, language]);

  const rollback = useCallback(async () => {
    try {
      const res = await gameAPI.rollback(userId);
      // Reload state after rollback
      await loadCurrentState();
      return res;
    } catch (err) {
      console.error('FinGame rollback error:', err);
      throw err;
    }
  }, [userId, loadCurrentState]);

  return {
    state: gameState,
    loading,
    startGame,
    loadCurrentState,
    makeChoice,
    rollback,
    setCurrentPath: (path) => setGameState(prev => ({ ...prev, currentPath: path })),
  };
}
