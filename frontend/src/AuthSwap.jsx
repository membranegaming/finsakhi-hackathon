import { useState } from "react";
import "./AuthSwap.css";

export default function AuthSwap({ onLogin }) {
  const [isSignup, setIsSignup] = useState(false);

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (onLogin) {
      onLogin();
    }
  };

  const handleSignupSubmit = (e) => {
    e.preventDefault();
    // After signup, redirect to assessment too
    if (onLogin) {
      onLogin();
    }
  };

  return (
    <div className="auth-wrapper">
      {/* Animated Background Bubbles */}
      <div className="bubbles">
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
      </div>

      <div className={`container ${isSignup ? "right-panel-active" : ""}`}>

        {/* SIGN UP FORM */}
        <div className="form-container sign-up-container">
          <form onSubmit={handleSignupSubmit}>
            <h2>Create Account</h2>

            <input type="text" placeholder="Name" />
            <input type="text" placeholder="Email or Phone no." />
            <input type="text" placeholder="Username" />
            <input type="password" placeholder="Password" />

            <div className="terms">
              <input type="checkbox" id="terms" />
              <label htmlFor="terms">I agree to all terms and Privacy Policy</label>
            </div>

            <button type="submit" className="primary-btn"> Create Account </button>

            <p className="switch-text mobile-only">
              Already have an account?{" "}
              <span onClick={() => setIsSignup(false)}>Log in</span>
            </p>
          </form>
        </div>

        {/* SIGN IN FORM */}
        <div className="form-container sign-in-container">
          <form onSubmit={handleLoginSubmit}>
            <h2>Welcome Back</h2>

            <input type="text" placeholder="Email or Username" />
            <input type="password" placeholder="Password" />

            <a href="#" className="forgot-link">Forgot your password?</a>

            <button type="submit" className="primary-btn"> Login </button>

            <p className="switch-text mobile-only">
              Don't have an account?{" "}
              <span onClick={() => setIsSignup(true)}>Sign up</span>
            </p>
          </form>
        </div>

        {/* OVERLAY PANELS */}
        <div className="overlay-container">
          <div className="overlay">

            <div className="overlay-panel overlay-left">
              <h2>Welcome Back!</h2>
              <p>To keep connected with us, please login with your personal info</p>
              <button className="ghost-btn" onClick={() => setIsSignup(false)}>
                Sign In
              </button>
            </div>

            <div className="overlay-panel overlay-right">
              <h2>Hello, Friend!</h2>
              <p>Enter your details and start your journey with us</p>
              <button className="ghost-btn" onClick={() => setIsSignup(true)}>
                Sign Up
              </button>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
