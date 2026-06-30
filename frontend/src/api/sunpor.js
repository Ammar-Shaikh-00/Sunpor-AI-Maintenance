function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_URL;

  if (configured !== undefined && configured !== "") {
    return configured.replace(/\/$/, "");
  }

  if (import.meta.env.DEV) {
    return "/api";
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }

  return "http://localhost:8000";
}

export const API_BASE_URL = resolveApiBaseUrl();

const ACCESS_TOKEN_KEY = "access_token";

let accessToken = null;

if (typeof window !== "undefined") {
  accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token) {
  accessToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem(ACCESS_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
  }
}

export function getAccessToken() {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (stored !== accessToken) {
      accessToken = stored;
    }
  }
  return accessToken;
}

export const ENDPOINTS = {
  health: "/health/live",
  appInfo: "/public/app-info",
  login: "/auth/login",
  me: "/auth/me",
  logout: "/auth/logout",
  formOptions: "/form-options",
  productionRuns: "/production-runs",
  productionEvents: "/production-events",
  materialBehavior: "/material-behavior-events",
  materialBlocks: "/material-blocks",
  dailyQuality: "/daily-quality-inputs",
  signalCatalog: "/signal-catalog",
  signalLatest: "/signal-timeseries/latest",
};
