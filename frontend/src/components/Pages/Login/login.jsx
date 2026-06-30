import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../../context/authContext";
import { useAppBranding } from "../../../store/backendStore";
import DemoCredentials from "./demoCredentials";

const STATUS_COLORS = {
  checking: "text-amber-600",
  online: "text-emerald-600",
  offline: "text-red-500",
};

export default function Login() {
  const { t } = useTranslation();
  const { appName, tagline, companyName, backendStatus } = useAppBranding();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const validateEmail = (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value);
  };

  const validatePassword = (value) => value.length >= 3;

  const handleEmailChange = (e) => {
    const value = e.target.value;
    setEmail(value);
    if (value && !validateEmail(value)) {
      setEmailError(t("login.invalidEmail"));
    } else {
      setEmailError("");
    }
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setPassword(value);
    if (value && !validatePassword(value)) {
      setPasswordError(t("login.passwordMinLength"));
    } else {
      setPasswordError("");
    }
  };

  const resolveLoginError = (err) => {
    if (!err.response) {
      return t("login.backendNotResponding");
    }

    if (err.response.status === 401) {
      return t("login.invalidCredentials");
    }

    if (err.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (typeof detail === "string") {
        return detail;
      }
      if (Array.isArray(detail)) {
        return detail.map((item) => item.msg).join(", ");
      }
    }

    return t("login.loginFailed");
  };

  const statusLabel = t(`login.status.${backendStatus}`, {
    defaultValue: backendStatus,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setEmailError("");
    setPasswordError("");

    if (!email) {
      setEmailError(t("login.emailRequired"));
      return;
    }
    if (!validateEmail(email)) {
      setEmailError(t("login.invalidEmail"));
      return;
    }
    if (!password) {
      setPasswordError(t("login.passwordRequired"));
      return;
    }
    if (!validatePassword(password)) {
      setPasswordError(t("login.passwordMinLength"));
      return;
    }

    if (backendStatus === "offline") {
      setError(t("login.backendNotResponding"));
      return;
    }

    setIsLoading(true);

    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(resolveLoginError(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-[#f7f5ff] to-[#efe9ff] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-700 to-purple-500 mb-2">
            {appName}
          </h1>
          <p className="text-slate-600 text-sm">
            {tagline || t("login.tagline")}
          </p>
        </div>

        <div className="bg-white/90 backdrop-blur-xl border border-slate-200 rounded-2xl p-8 shadow-xl">
          <h2 className="text-2xl font-semibold text-slate-900 mb-6 text-center">
            {t("login.signIn")}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/20 border border-rose-500/50 rounded-lg text-red-600 text-sm">
              <div className="flex items-center gap-2">
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                {t("login.email")}
              </label>
              <input
                type="email"
                value={email}
                onChange={handleEmailChange}
                className="w-full px-4 py-3 border rounded-xl"
                placeholder={t("login.emailPlaceholder")}
                disabled={isLoading}
              />
              {emailError && (
                <p className="text-xs text-red-500">{emailError}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                {t("login.password")}
              </label>
              <input
                type="password"
                value={password}
                onChange={handlePasswordChange}
                className="w-full px-4 py-3 border rounded-xl"
                disabled={isLoading}
              />
              {passwordError && (
                <p className="text-xs text-red-500">{passwordError}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={
                isLoading ||
                emailError ||
                passwordError ||
                backendStatus === "checking"
              }
              className="w-full py-3 bg-purple-600 text-white rounded-xl disabled:opacity-60"
            >
              {isLoading ? t("login.signingIn") : t("login.signIn")}
            </button>
          </form>

          <DemoCredentials companyName={companyName} />

          <div
            className={`mt-6 pt-6 border-t border-slate-200 text-xs text-center ${STATUS_COLORS[backendStatus] || "text-slate-500"}`}
          >
            {t("login.backendStatus")}: {statusLabel}
          </div>
        </div>
      </div>
    </div>
  );
}
