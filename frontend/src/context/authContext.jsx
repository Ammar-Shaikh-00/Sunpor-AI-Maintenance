import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
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
      setUser(response.data);
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

  const permissions = useMemo(
    () => new Set(user?.permissions || []),
    [user?.permissions]
  );

  const hasPermission = useCallback(
    (permissionCode) => {
      if (!permissionCode) return true;
      return (
        permissions.has(permissionCode) || permissions.has("system.admin")
      );
    },
    [permissions]
  );

  const hasAnyPermission = useCallback(
    (permissionCodes = []) => {
      if (!permissionCodes.length) return true;
      return permissionCodes.some((code) => hasPermission(code));
    },
    [hasPermission]
  );

  const roleLabel = useMemo(() => {
    if (!user?.roles?.length) return "USER";
    return user.roles.map((role) => role.name).join(", ");
  }, [user?.roles]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        refreshUser: fetchUserProfile,
        isAuthenticated: !!token,
        isLoading,
        hasPermission,
        hasAnyPermission,
        roleLabel,
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
