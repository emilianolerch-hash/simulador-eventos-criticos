'use client';

import { useState } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useAuth } from '@/hooks/useAuth';
import { Disclaimer } from '@/components/Disclaimer';
import { VitalMonitor } from '@/components/VitalMonitor';
import { PatientInfo } from '@/components/PatientInfo';
import { ActionPanel } from '@/components/ActionPanel';
import { Timeline } from '@/components/Timeline';
import { DebriefScreen } from '@/components/DebriefScreen';
import { LoginModal } from '@/components/LoginModal';

const SCENARIO_ID = 'anaphylaxis_perioperative_adult_v1';

export default function Home() {
  const {
    view, session, scenario, debrief, log,
    loading, error,
    isLive, liveInterval, setLiveInterval,
    start, applyAction, advanceTime, toggleLive, restart, clearError,
  } = useSimulation();

  const { user, error: authError, login, register, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  // ── Debrief view ──
  if (view === 'debrief' && debrief) {
    return <DebriefScreen debrief={debrief} onRestart={restart} />;
  }

  // ── Home / loading ──
  if (view === 'home') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col">
        <Disclaimer />

        {/* Top nav */}
        <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-end gap-3">
          {user ? (
            <>
              <span className="text-xs text-slate-400">{user.full_name}</span>
              {user.role === 'validator' && (
                <a href="/admin" className="text-xs text-blue-400 hover:underline">
                  Panel de validación
                </a>
              )}
              <button onClick={logout} className="text-xs text-red-400 hover:underline">Salir</button>
            </>
          ) : (
            <button
              onClick={() => setShowLogin(true)}
              className="text-xs text-slate-400 hover:text-white underline"
            >
              Iniciar sesión
            </button>
          )}
        </div>

        {showLogin && (
          <LoginModal
            onLogin={login}
            onRegister={register}
            onClose={() => setShowLogin(false)}
            error={authError}
          />
        )}

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="max-w-md w-full text-center space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Simulador de Eventos Críticos
              </h1>
              <p className="text-slate-400 text-sm mt-2">
                Herramienta educativa para entrenamiento en anestesiología
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-left">
              <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">
                Escenario disponible
              </div>
              <div className="text-sm font-semibold text-slate-200">
                Anafilaxia Perioperatoria — Paciente Adulto
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Dificultad alta · Anestesiología · Urgencia
              </div>
            </div>

            {error && (
              <div className="bg-red-950 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300 text-left">
                {error}
                <button onClick={clearError} className="ml-2 underline text-red-400 text-xs">Cerrar</button>
              </div>
            )}

            <button
              onClick={() => start(SCENARIO_ID)}
              disabled={loading}
              className="w-full bg-blue-700 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-wait
                         text-white font-semibold py-3 rounded-xl text-sm transition-colors"
            >
              {loading ? 'Iniciando...' : 'Comenzar simulación'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Simulation view ──
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Disclaimer />

      {/* Title bar */}
      <div className="px-4 py-2 flex items-center justify-between border-b border-slate-800">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-2">
          Anafilaxia Perioperatoria
          {isLive && (
            <span className="inline-flex items-center gap-1 text-green-400 font-bold">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              LIVE
            </span>
          )}
        </span>
        <div className="flex items-center gap-3">
          {loading && (
            <span className="text-[10px] text-cyan-400 animate-pulse">Procesando...</span>
          )}
          {user && (
            <span className="text-[10px] text-slate-500">{user.full_name}</span>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-950 border-b border-red-700 px-4 py-2 flex items-center justify-between">
          <span className="text-xs text-red-300">{error}</span>
          <button onClick={clearError} className="text-red-400 text-xs underline ml-4">Cerrar</button>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 py-4 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">

          {/* Left column */}
          <div className="space-y-4">
            <VitalMonitor
              vitals={session?.vitals}
              simTime={session?.sim_time_seconds ?? 0}
            />
            <PatientInfo scenario={scenario} session={session} />
            <ActionPanel
              session={session}
              scenario={scenario}
              onAction={applyAction}
              onAdvanceTime={advanceTime}
              loading={loading}
              isLive={isLive}
              liveInterval={liveInterval}
              onSetLiveInterval={setLiveInterval}
              onToggleLive={toggleLive}
            />
          </div>

          {/* Right column */}
          <div className="flex flex-col min-h-0 h-full">
            <Timeline log={log} />
          </div>

        </div>
      </div>
    </div>
  );
}
