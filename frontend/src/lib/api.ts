import type { SessionState, ScenarioDetail, DebriefReport, ActionLogEntry, ValidationRecord } from './types';
import { loadToken } from './auth';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function authHeaders(): Record<string, string> {
  const token = loadToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...(init?.headers as Record<string, string> ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listScenarios: () =>
    request<{ id: string; title: string }[]>('/scenarios'),

  getScenario: (id: string) =>
    request<ScenarioDetail>(`/scenarios/${id}`),

  createSession: (scenario_id: string) =>
    request<SessionState>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ scenario_id }),
    }),

  getState: (sid: string) =>
    request<SessionState>(`/sessions/${sid}/state`),

  applyAction: (sid: string, action_id: string) =>
    request<SessionState>(`/sessions/${sid}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action_id }),
    }),

  advanceTime: (sid: string, seconds: number) =>
    request<SessionState>(`/sessions/${sid}/advance-time`, {
      method: 'POST',
      body: JSON.stringify({ seconds }),
    }),

  getLog: (sid: string) =>
    request<{ total_entries: number; action_log: ActionLogEntry[] }>(
      `/sessions/${sid}/log`,
    ),

  getDebrief: (sid: string) =>
    request<DebriefReport>(`/sessions/${sid}/debrief`),

  getPdfUrl: (sid: string) => `${BASE}/sessions/${sid}/pdf`,

  listValidations: (scenario_id?: string) => {
    const q = scenario_id ? `?scenario_id=${encodeURIComponent(scenario_id)}` : '';
    return request<ValidationRecord[]>(`/admin/validations${q}`);
  },

  createValidation: (data: {
    scenario_id: string;
    rule_ref: string;
    rule_description: string;
    notes?: string;
  }) =>
    request<ValidationRecord>('/admin/validations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteValidation: (id: string) =>
    fetch(`${BASE}/admin/validations/${id}`, {
      method: 'DELETE',
      headers: { ...authHeaders() },
    }),
};
