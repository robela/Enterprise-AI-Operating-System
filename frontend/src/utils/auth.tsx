"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { apiClient } from "@/services/api/client";
import type { UserRole } from "./types";

interface AccessTokenPayload {
  sub?: string;
  roles?: string[];
}

interface AuthContextType {
  token: string | null;
  username: string | null;
  user_id: string | null;
  role: UserRole | null;
  isLoading: boolean;
  loginError: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function decodeAccessTokenPayload(token: string): AccessTokenPayload | null {
  try {
    const [, payload] = token.split(".");

    if (!payload) {
      return null;
    }

    const normalizedPayload = payload.replace(/-/g, "+").replace(/_/g, "/");
    const paddedPayload = normalizedPayload.padEnd(
      normalizedPayload.length + ((4 - (normalizedPayload.length % 4)) % 4),
      "="
    );

    return JSON.parse(atob(paddedPayload)) as AccessTokenPayload;
  } catch {
    return null;
  }
}

function resolveRole(accessToken: string, roleFromResponse?: string): UserRole | null {
  if (roleFromResponse === "admin" || roleFromResponse === "user" || roleFromResponse === "callAgent") {
    return roleFromResponse;
  }

  const payload = decodeAccessTokenPayload(accessToken);
  const tokenRoles = payload?.roles ?? [];

  if (tokenRoles.includes("admin")) {
    return "admin";
  }

  if (tokenRoles.includes("callAgent")) {
    return "callAgent";
  }

  if (tokenRoles.includes("user")) {
    return "user";
  }

  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [user_id, setUserId] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Restore session from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedUsername = localStorage.getItem("username");
    const storedRole = localStorage.getItem("role") as UserRole | null;
    const storedUserId = localStorage.getItem("user_id");

    if (storedToken) {
      setToken(storedToken);
      setUsername(storedUsername);
      setRole(storedRole ?? resolveRole(storedToken));
      setUserId(storedUserId);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (usernameInput: string, password: string) => {
    setLoginError(null);
    const params = new URLSearchParams();
    params.append("username", usernameInput);
    params.append("password", password);

    const { data } = await apiClient.post("/api/v1/auth/token", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    const { access_token, username: uname, user_id: uid, role: urole } = data;
    const resolvedRole = resolveRole(access_token, urole);
    const resolvedUserId = typeof uid === "string" ? uid : decodeAccessTokenPayload(access_token)?.sub ?? null;

    localStorage.setItem("token", access_token);
    localStorage.setItem("username", uname ?? usernameInput);
    if (resolvedRole) {
      localStorage.setItem("role", resolvedRole);
    } else {
      localStorage.removeItem("role");
    }
    if (resolvedUserId) {
      localStorage.setItem("user_id", resolvedUserId);
    } else {
      localStorage.removeItem("user_id");
    }

    setToken(access_token);
    setUsername(uname ?? usernameInput);
    setRole(resolvedRole);
    setUserId(resolvedUserId);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");
    localStorage.removeItem("user_id");
    setToken(null);
    setUsername(null);
    setRole(null);
    setUserId(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, username, user_id, role, isLoading, loginError, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
