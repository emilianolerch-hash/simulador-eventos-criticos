import type { UserOut, TokenOut } from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const authApi = {
  register: (email: string, password: string, full_name: string, role = 'anesthesiologist') =>
    request<TokenOut>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name, role }),
    }),

  login: (email: string, password: string) =>
    request<TokenOut>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) =>
    request<UserOut>('/auth/me', {
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    }),
};

export function saveToken(token: string): void {
  if (typeof window !== 'undefined') localStorage.setItem('auth_token', token);
}

export function loadToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export function clearToken(): void {
  if (typeof window !== 'undefined') localStorage.removeItem('auth_token');
}
