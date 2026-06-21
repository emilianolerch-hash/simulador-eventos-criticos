'use client';
import type { SessionState, ScenarioDetail } from '@/lib/types';

const STATE_META: Record<string, { label: string; color: string; bg: string }> = {
  INITIAL_PRESENTATION:            { label: 'Presentación inicial',   color: 'text-slate-300',   bg: 'bg-slate-800' },
  GRADE_I:                         { label: 'Grado I — Cutáneo',      color: 'text-yellow-400',  bg: 'bg-yellow-950' },
  GRADE_II:                        { label: 'Grado II — Sistémico',   color: 'text-orange-400',  bg: 'bg-orange-950' },
  GRADE_III:                       { label: 'Grado III — Colapso',    color: 'text-red-500',     bg: 'bg-red-950' },
  GRADE_IV:                        { label: '⚡ PARO CARDÍACO',       color: 'text-red-400',     bg: 'bg-red-950 border border-red-600 animate-pulse' },
  RESOLVING:                       { label: 'En resolución ↑',        color: 'text-green-400',   bg: 'bg-green-950' },
  RESOLVING_AFTER_CPR:             { label: 'Post-RCP (ROSC)',        color: 'text-blue-400',    bg: 'bg-blue-950' },
  OUTCOME_FULL_RECOVERY:           { label: 'Recuperación completa',  color: 'text-green-400',   bg: 'bg-green-950' },
  OUTCOME_CARDIAC_ARREST_WITH_RECOVERY: { label: 'Paro con recuperación', color: 'text-yellow-400', bg: 'bg-yellow-950' },
  OUTCOME_DEATH:                   { label: 'Fallecimiento',          color: 'text-red-400',     bg: 'bg-red-950' },
};

export function PatientInfo({
  scenario,
  session,
}: {
  scenario: ScenarioDetail | null;
  session: SessionState | null;
}) {
  if (!scenario || !session) return null;

  const meta = STATE_META[session.state] ?? {
    label: session.state,
    color: 'text-slate-300',
    bg: 'bg-slate-800',
  };
  const p = scenario.patient;

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 space-y-4">
      {/* Patient header */}
      <div>
        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">
          Paciente
        </div>
        <div className="text-sm text-slate-200 font-medium">
          {p.sex === 'male' ? 'Hombre' : 'Mujer'} · {p.age} años · {p.weight_kg} kg · ASA {p.asa_class}
        </div>
        <div className="text-xs text-slate-400 mt-1 leading-snug">{p.context}</div>
      </div>

      {/* Clinical state badge */}
      <div>
        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">
          Estado clínico
        </div>
        <div className={`rounded-lg px-3 py-2 ${meta.bg}`}>
          <div className={`text-sm font-bold ${meta.color}`}>{meta.label}</div>
          <div className="text-xs text-slate-300 mt-1 leading-relaxed">
            {session.state_description}
          </div>
        </div>
      </div>
    </div>
  );
}
