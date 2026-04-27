import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, clearToken, getToken, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTok] = useState(() => getToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const me = await api("/api/users/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email, password) => {
    const res = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    setTok(res.access_token);
    await refreshUser();
  }, [refreshUser]);

  const signup = useCallback(
    async ({ email, full_name, password }) => {
      await api("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, full_name, password }),
      });
      // Backend signup returns user (not token), so we login right after.
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearToken();
    setTok(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      refreshUser,
      isAuthenticated: Boolean(token),
      signup,
    }),
    [token, user, loading, login, logout, refreshUser, signup],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
