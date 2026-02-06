import { useState } from 'react'
import { AppProvider } from './contexts/AppContext'
import { AuthProvider, useAuth } from './store/authStore.jsx'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Assessment from './pages/Assessment'
import Dashboard from './pages/Dashboard'
import CandleLoader from './components/ui/CandleLoader'

function AppContent() {
  const { isAuthenticated, userName, userLevel, login, logout, setLevel, updateName, userId } = useAuth();
  const [currentPage, setCurrentPage] = useState(isAuthenticated ? 'dashboard' : 'login');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (authData) => {
    // authData = { token, user_id, name, language, total_xp, level } from backend
    login(authData);
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      // If user has no assessment level yet, go to assessment
      if (!authData.literacy_level) {
        setCurrentPage('assessment');
      } else {
        setLevel(authData.literacy_level);
        setCurrentPage('dashboard');
      }
    }, 2500);
  };

  const [initialSection, setInitialSection] = useState(null);

  const handleAssessmentComplete = (level) => {
    setLevel(level);
    setInitialSection('learning');
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    logout();
    setCurrentPage('login');
  };

  if (isLoading) {
    return <CandleLoader fullscreen message="Growing your financial journey..." />;
  }

  if (!isAuthenticated) {
    switch (currentPage) {
      case 'signup':
        return <Signup onLogin={handleLogin} onSwitchToLogin={() => setCurrentPage('login')} />;
      case 'login':
      default:
        return <Login onLogin={handleLogin} onSwitchToSignup={() => setCurrentPage('signup')} />;
    }
  }

  // Authenticated pages
  switch (currentPage) {
    case 'assessment':
      return <Assessment onComplete={handleAssessmentComplete} userName={userName} userId={userId} />;
    case 'dashboard':
    default:
      return (
        <Dashboard
          onLogout={handleLogout}
          initialSection={initialSection}
        />
      );
  }
}

function App() {
  return (
    <AppProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </AppProvider>
  );
}

export default App

