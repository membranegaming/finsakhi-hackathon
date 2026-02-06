import AuthForm from "../components/auth/AuthForm";

export default function Signup({ onLogin }) {
  return <AuthForm onLogin={onLogin} initialMode="signup" />;
}

