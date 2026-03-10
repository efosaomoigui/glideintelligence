"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface UserProfile {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  role: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (userData: any, token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage on mount
    const storedUser = localStorage.getItem("gl_intel_user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse stored user", e);
      }
    }
    
    // Also verify with backend to ensure session is valid
    fetch("/api/auth/me")
      .then(res => {
        if (res.ok) return res.json();
        throw new Error("Session invalid");
      })
      .then(data => {
        setUser(data);
        localStorage.setItem("gl_intel_user", JSON.stringify(data));
      })
      .catch(() => {
        // If /me fails, clear local user if any (session might have expired)
        // setUser(null);
        // localStorage.removeItem("gl_intel_user");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = (userData: any, token: string) => {
    setUser(userData);
    localStorage.setItem("gl_intel_user", JSON.stringify(userData));
    // Token is usually in a cookie, but we can store it in localStorage if needed for non-secure contexts
    // localStorage.setItem("gl_intel_token", token);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("gl_intel_user");
    // Hit logout endpoint to clear cookies
    fetch("/api/auth/logout", { method: "POST" }).finally(() => {
        window.location.reload(); // Refresh to clear states
    });
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
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
