'use client';
import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import type { SessionState, ScenarioDetail, DebriefReport, ActionLogEntry } from '@/lib/types';

type SimView = 'home' | 'simulating' | 'debrief';

export const LIVE_INTERVAL_OPTIONS = [3, 5, 10, 15] as const;
export type LiveInterval = typeof LIVE_INTERVAL_OPTIONS[number];

export function useSimulation() {
  const [view, setView] = useState<SimView>('home');
  const [session, setSession] = useState<SessionState | null>(null);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [debrief, setDebrief] = useState<DebriefReport | null>(null);
  const [log, setLog] = useState<ActionLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live mode
  const [isLive, setIsLive] = useState(false);
  const [liveInterval, setLiveInterval] = useState<LiveInterval>(5);

  const startingRef = useRef(false);
  const loadingRef = useRef(false);
  const sessionRef = useRef<SessionState | null>(null);
  const liveTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { loadingRef.current = loading; }, [loading]);
  useEffect(() => { sessionRef.current = session; }, [session]);

  const clearError = useCallback(() => setError(null), []);

  const _stopLive = useCallback(() => {
    if (liveTimerRef.current !== null) {
      clearInterval(liveTimerRef.current);
      liveTimerRef.current = null;
    }
    setIsLive(false);
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
      _stopLive();
      try {
        const d = await api.getDebrief(state.session_id);
        setDebrief(d);
        setView('debrief');
      } catch {
        setError('Error al obtener el debriefing.');
      }
    }
  }, [_stopLive]);

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
    } catch {
      setError('No se pudo conectar con el motor clínico. Verificá que el backend esté activo en http://localhost:8000');
    } finally {
      setLoading(false);
      startingRef.current = false;
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
    _stopLive();
    if (!scenario) return;
    setView('home');
    await start(scenario.id);
  }, [scenario, start, _stopLive]);

  const toggleLive = useCallback(() => {
    if (isLive) {
      _stopLive();
      return;
    }
    if (!session || session.is_terminal) return;

    const timer = setInterval(() => {
      if (loadingRef.current || !sessionRef.current || sessionRef.current.is_terminal) {
        return;
      }
      const sid = sessionRef.current.session_id;
      loadingRef.current = true;
      setLoading(true);
      api.advanceTime(sid, 15)
        .then(async (state) => {
          setSession(state);
          sessionRef.current = state;
          if (state.is_terminal) {
            _stopLive();
            try {
              const d = await api.getDebrief(state.session_id);
              setDebrief(d);
              setView('debrief');
            } catch {
              setError('Error al obtener el debriefing.');
            }
          }
        })
        .catch((e: unknown) => {
          setError(e instanceof Error ? e.message : 'Error en modo live.');
        })
        .finally(() => {
          loadingRef.current = false;
          setLoading(false);
        });
    }, liveInterval * 1000);

    liveTimerRef.current = timer;
    setIsLive(true);
  }, [isLive, session, liveInterval, _stopLive]);

  // Auto-stop when session ends externally (e.g. via applyAction)
  useEffect(() => {
    if (session?.is_terminal && isLive) {
      _stopLive();
    }
  }, [session?.is_terminal, isLive, _stopLive]);

  // Cleanup on unmount
  useEffect(() => () => { _stopLive(); }, [_stopLive]);

  return {
    view, session, scenario, debrief, log, loading, error,
    isLive, liveInterval, setLiveInterval,
    start, applyAction, advanceTime, toggleLive, restart, clearError,
  };
}
