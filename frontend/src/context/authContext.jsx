import React, { createContext, useContext, useEffect, useState } from "react";
import api, { getAccessToken, setAccessToken } from "../api";
import { ENDPOINTS } from "../api/sunpor";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getAccessToken());
  const [isLoading, setIsLoading] = useState(true);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get(ENDPOINTS.me);
      setUser({
        ...response.data,
        role: "operator",
      });
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      setUser(null);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const existingToken = getAccessToken();
      if (existingToken) {
        setToken(existingToken);
        await fetchUserProfile();
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.post(ENDPOINTS.login, {
      email,
      password,
    });

    const { access_token } = response.data;
    setToken(access_token);
    setAccessToken(access_token);
    await fetchUserProfile();
  };

  const logout = async () => {
    try {
      await api.post(ENDPOINTS.logout);
    } catch {
      // ignore logout errors
    }

    setToken(null);
    setUser(null);
    setAccessToken(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
