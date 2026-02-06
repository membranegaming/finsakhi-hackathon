import { useState } from "react";
import { useApp } from "../../contexts/AppContext";
import { authAPI } from "../../services/api";
import LanguageToggle from "../ui/LanguageToggle";
import ThemeToggle from "../ui/ThemeToggle";
import "./AuthForm.css";

export default function AuthForm({ onLogin, initialMode = "login" }) {
  const { t, language } = useApp();
  const [isSignup, setIsSignup] = useState(initialMode === "signup");

  // Phone + OTP flow
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [step, setStep] = useState("phone"); // "phone" | "otp"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [demoOtp, setDemoOtp] = useState(""); // shown in demo mode

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!phone.trim() || phone.length !== 10) {
      setError(language === 'hi' ? 'कृपया 10 अंकों का मोबाइल नंबर दर्ज करें' : 'Please enter a valid 10-digit mobile number');
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await authAPI.sendOTP(phone.startsWith("+") ? phone : `+91${phone}`, language);
      if (res.otp) setDemoOtp(res.otp); // demo mode shows OTP
      setStep("otp");
    } catch (err) {
      setError(err.message || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otp.trim()) return;
    setError("");
    setLoading(true);
    try {
      const fullPhone = phone.startsWith("+") ? phone : `+91${phone}`;
      const res = await authAPI.verifyOTP(fullPhone, otp, name || null);
      // res = { token, user_id, name, language, total_xp, level, message }
      if (onLogin) onLogin(res);
    } catch (err) {
      setError(err.message || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  const resetFlow = () => {
    setStep("phone");
    setOtp("");
    setDemoOtp("");
    setError("");
  };

  return (
    <div className="auth-wrapper">
      <div className="money-symbols">
        <div className="money-symbol">₹</div>
        <div className="money-symbol">$</div>
        <div className="money-symbol">€</div>
        <div className="money-symbol">£</div>
        <div className="money-symbol">¥</div>
        <div className="money-symbol">₹</div>
        <div className="money-symbol">$</div>
        <div className="money-symbol">€</div>
      </div>

      <div className="controls-bar">
        <LanguageToggle />
        <ThemeToggle />
      </div>

      <div className="auth-card">
        <div className="auth-forms-container">
          <div className="auth-forms-slider show-login">
            <div className="auth-panel">
              <div className="auth-header-section">
                <div className="header-content">
                  <div className="auth-logo">
                    <svg viewBox="0 0 60 60" className="logo-svg">
                      <circle cx="30" cy="30" r="28" fill="#FFFFFF" opacity="0.2" />
                      <text x="30" y="38" textAnchor="middle" fill="#FFFFFF" fontSize="24" fontWeight="bold">₹</text>
                    </svg>
                  </div>
                  <h1 className="auth-title">FinSakhi</h1>
                  <p className="auth-subtitle">
                    {language === 'hi' ? 'अपने मोबाइल नंबर से लॉगिन करें' : 'Login with your mobile number'}
                  </p>
                </div>
              </div>

              <div className="auth-divider"></div>

              <div className="auth-form-section">
                {step === "phone" ? (
                  <form onSubmit={handleSendOTP}>
                    {isSignup && (
                      <div className="input-group">
                        <label className="input-label">{language === 'hi' ? 'नाम' : 'Name'}</label>
                        <input
                          type="text"
                          placeholder={language === 'hi' ? 'अपना नाम दर्ज करें' : 'Enter your name'}
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                        />
                      </div>
                    )}
                    <div className="input-group">
                      <label className="input-label">{language === 'hi' ? 'मोबाइल नंबर' : 'Mobile Number'}</label>
                      <div className="phone-input-wrapper">
                        <span className="phone-prefix">
                          <span className="phone-flag">🇮🇳</span>
                          <span className="phone-code">+91</span>
                        </span>
                        <input
                          type="tel"
                          className="phone-number-input"
                          placeholder={language === 'hi' ? '98765 43210' : '98765 43210'}
                          value={phone}
                          onChange={(e) => {
                            const digits = e.target.value.replace(/\D/g, '').slice(0, 10);
                            setPhone(digits);
                          }}
                          required
                          maxLength={10}
                          inputMode="numeric"
                          pattern="[0-9]*"
                          autoComplete="tel-national"
                        />
                      </div>
                    </div>
                    {error && <p style={{ color: '#e74c3c', fontSize: '0.85rem', margin: '0.5rem 0' }}>{error}</p>}
                    <button type="submit" className="primary-btn" disabled={loading}>
                      {loading ? '...' : (language === 'hi' ? 'OTP भेजें' : 'Send OTP')}
                    </button>
                    <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {isSignup ? (
                        <span>
                          {language === 'hi' ? 'पहले से खाता है?' : 'Already have an account?'}{' '}
                          <a href="#" onClick={(e) => { e.preventDefault(); setIsSignup(false); }}
                            style={{ color: 'var(--accent-primary)' }}>
                            {language === 'hi' ? 'लॉगिन करें' : 'Login'}
                          </a>
                        </span>
                      ) : (
                        <span>
                          {language === 'hi' ? 'नया खाता?' : 'New user?'}{' '}
                          <a href="#" onClick={(e) => { e.preventDefault(); setIsSignup(true); }}
                            style={{ color: 'var(--accent-primary)' }}>
                            {language === 'hi' ? 'अभी रजिस्टर करें' : 'Register now'}
                          </a>
                        </span>
                      )}
                    </p>
                  </form>
                ) : (
                  <form onSubmit={handleVerifyOTP}>
                    <div className="input-group">
                      <label className="input-label">{language === 'hi' ? 'OTP दर्ज करें' : 'Enter OTP'}</label>
                      <input
                        type="text"
                        placeholder="______"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        required
                        maxLength={6}
                        style={{ textAlign: 'center', letterSpacing: '0.5rem', fontSize: '1.3rem' }}
                      />
                    </div>
                    {demoOtp && (
                      <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--accent-primary)', margin: '0.5rem 0' }}>
                        Demo OTP: <strong>{demoOtp}</strong>
                      </p>
                    )}
                    {error && <p style={{ color: '#e74c3c', fontSize: '0.85rem', margin: '0.5rem 0' }}>{error}</p>}
                    <button type="submit" className="primary-btn" disabled={loading}>
                      {loading ? '...' : (language === 'hi' ? 'OTP सत्यापित करें' : 'Verify OTP')}
                    </button>
                    <p style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                      <a href="#" onClick={(e) => { e.preventDefault(); resetFlow(); }}
                        style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        ← {language === 'hi' ? 'नंबर बदलें' : 'Change number'}
                      </a>
                    </p>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

