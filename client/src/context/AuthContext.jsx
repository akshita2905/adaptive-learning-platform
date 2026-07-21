import React, { createContext, useContext, useMemo, useState } from "react";

const AuthContext = createContext(null);

/**
 * Holds JWT and minimal user profile for the SPA.
 */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

  const login = (payload) => {
    localStorage.setItem("token", payload.access_token);
    const u = {
      email: payload.email,
      full_name: payload.full_name,
      user_id: payload.user_id,
    };
    localStorage.setItem("user", JSON.stringify(u));
    setToken(payload.access_token);
    setUser(u);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
