'use client';
import { useState, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import type { SessionState, ScenarioDetail, DebriefReport, ActionLogEntry } from '@/lib/types';

type SimView = 'home' | 'simulating' | 'debrief';

export function useSimulation() {
  const [view, setView] = useState<SimView>('home');
  const [session, setSession] = useState<SessionState | null>(null);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [debrief, setDebrief] = useState<DebriefReport | null>(null);
  const [log, setLog] = useState<ActionLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const startingRef = useRef(false);

  const clearError = useCallback(() => setError(null), []);

  const start = useCallback(async (scenarioId: string) => {
    if (startingRef.current) return;
    startingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const [scenarioData, sessionData] = await Promise.all([
        api.getScenario(scenarioId),
        api.createSession(scenarioId),
      ]);
      setScenario(scenarioData);
      setSession(sessionData);
      setLog([]);
      setDebrief(null);
      setView('simulating');
    } catch (e) {
      setError('No se pudo conectar con el motor clínico. Verificá que el backend esté activo en http://localhost:8000');
    } finally {
      setLoading(false);
      startingRef.current = false;
    }
  }, []);

  const _refreshLog = useCallback(async (sid: string) => {
    try {
      const { action_log } = await api.getLog(sid);
      setLog(action_log);
    } catch {
      // non-critical
    }
  }, []);

  const _checkTerminal = useCallback(async (state: SessionState) => {
    if (state.is_terminal && state.session_id) {
      try {
        const d = await api.getDebrief(state.session_id);
        setDebrief(d);
        setView('debrief');
      } catch {
        setError('Error al obtener el debriefing.');
      }
    }
  }, []);

  const applyAction = useCallback(async (actionId: string) => {
    if (!session || loading) return;
    setLoading(true);
    setError(null);
    try {
      const state = await api.applyAction(session.session_id, actionId);
      setSession(state);
      await _refreshLog(state.session_id);
      await _checkTerminal(state);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Acción no disponible en el estado actual.');
    } finally {
      setLoading(false);
    }
  }, [session, loading, _refreshLog, _checkTerminal]);

  const advanceTime = useCallback(async (seconds = 15) => {
    if (!session || loading) return;
    setLoading(true);
    setError(null);
    try {
      const state = await api.advanceTime(session.session_id, seconds);
      setSession(state);
      await _checkTerminal(state);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al avanzar el tiempo.');
    } finally {
      setLoading(false);
    }
  }, [session, loading, _checkTerminal]);

  const restart = useCallback(async () => {
    if (!scenario) return;
    setView('home');
    await start(scenario.id);
  }, [scenario, start]);

  return {
    view, session, scenario, debrief, log, loading, error,
    start, applyAction, advanceTime, restart, clearError,
  };
}
