'use client';
import { useState, useEffect, useCallback } from 'react';
import { authApi, saveToken, loadToken, clearToken } from '@/lib/auth';
import type { UserOut } from '@/lib/types';

export function useAuth() {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = loadToken();
    if (!stored) { setLoading(false); return; }
    authApi.me(stored)
      .then((u) => { setUser(u); setToken(stored); })
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const data = await authApi.login(email, password);
      saveToken(data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error de autenticación');
      throw e;
    }
  }, []);

  const register = useCallback(async (
    email: string, password: string, full_name: string, role: string
  ) => {
    setError(null);
    try {
      const data = await authApi.register(email, password, full_name, role);
      saveToken(data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al registrarse');
      throw e;
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setToken(null);
    setUser(null);
  }, []);

  return { user, token, loading, error, login, register, logout };
}
