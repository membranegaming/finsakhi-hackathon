/**
 * Auth store — persists user session to localStorage
 */
import { createContext, useContext, useState, useCallback, useEffect } from "react";

const AuthContext = createContext(null);
const STORAGE_KEY = 'finsakhi_auth';

function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveSession(data) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  else localStorage.removeItem(STORAGE_KEY);
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadSession);

  const user = session || null;
  const isAuthenticated = !!session;
  const userId = session?.user_id || null;
  const token = session?.token || null;
  const userName = session?.name || 'User';
  const userLevel = session?.level || null;

  // Persist whenever session changes
  useEffect(() => { saveSession(session); }, [session]);

  const login = useCallback((data) => {
    // data = { token, user_id, name, language, total_xp, level }
    setSession(data);
  }, []);

  const logout = useCallback(() => {
    setSession(null);
  }, []);

  const setLevel = useCallback((level) => {
    setSession(prev => prev ? { ...prev, level } : prev);
  }, []);

  const updateName = useCallback((name) => {
    setSession(prev => prev ? { ...prev, name } : prev);
  }, []);

  const value = {
    user, isAuthenticated, userId, token, userName, userLevel,
    login, logout, setLevel, updateName,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}

export default { AuthProvider, useAuth };

