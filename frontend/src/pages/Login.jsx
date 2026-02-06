import AuthForm from "../components/auth/AuthForm";

export default function Login({ onLogin }) {
  return <AuthForm onLogin={onLogin} initialMode="login" />;
}

