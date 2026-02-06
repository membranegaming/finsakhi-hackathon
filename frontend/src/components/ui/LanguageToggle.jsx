import { useApp } from '../../contexts/AppContext';
import './LanguageToggle.css';

function LanguageToggle() {
  const { language, toggleLanguage } = useApp();

  return (
    <div className="language-toggle">
      <button
        className={`lang-btn ${language === 'en' ? 'active' : ''}`}
        onClick={toggleLanguage}
        aria-label="Switch to English"
      >
        EN
      </button>
      <button
        className={`lang-btn ${language === 'hi' ? 'active' : ''}`}
        onClick={toggleLanguage}
        aria-label="Switch to Hindi"
      >
        HI
      </button>
    </div>
  );
}

export default LanguageToggle;

