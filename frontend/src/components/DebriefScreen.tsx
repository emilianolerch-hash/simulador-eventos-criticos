'use client';
import type { DebriefReport } from '@/lib/types';
import { Disclaimer } from './Disclaimer';
import { api } from '@/lib/api';

const OUTCOME_COLOR: Record<string, string> = {
  OUTCOME_FULL_RECOVERY:               'text-green-400',
  OUTCOME_CARDIAC_ARREST_WITH_RECOVERY:'text-yellow-400',
  OUTCOME_DEATH:                       'text-red-400',
};

function fmtTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

export function DebriefScreen({
  debrief,
  onRestart,
}: {
  debrief: DebriefReport;
  onRestart: () => void;
}) {
  const color = OUTCOME_COLOR[debrief.outcome_id] ?? 'text-slate-200';
  const { sections } = debrief;

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Disclaimer />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full px-4 py-8 space-y-6">

          {/* Outcome header */}
          <div className="text-center">
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">
              Debriefing — Anafilaxia Perioperatoria
            </div>
            <h1 className={`text-3xl font-bold ${color}`}>{debrief.outcome_label}</h1>
            <p className="text-slate-400 text-sm mt-2">{debrief.outcome_description}</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest">Tiempo simulado</div>
              <div className="text-3xl font-mono text-cyan-400 font-bold mt-1">
                {fmtTime(debrief.total_sim_time_seconds)}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest">Acciones realizadas</div>
              <div className="text-3xl font-mono text-cyan-400 font-bold mt-1">
                {debrief.total_actions_taken}
              </div>
            </div>
          </div>

          {/* Correct / Missed */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs font-bold text-green-400 uppercase tracking-wider mb-3">
                ✓ Acciones correctas
              </div>
              {sections.correct_actions.length === 0 ? (
                <p className="text-xs text-slate-500 italic">Ninguna</p>
              ) : (
                sections.correct_actions.map((a, i) => (
                  <div key={i} className="text-xs text-slate-200 py-0.5 flex gap-2">
                    <span className="text-green-500">✓</span>{a}
                  </div>
                ))
              )}
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs font-bold text-red-400 uppercase tracking-wider mb-3">
                ✗ Acciones omitidas
              </div>
              {sections.missed_actions.length === 0 ? (
                <p className="text-xs text-slate-500 italic">Ninguna</p>
              ) : (
                sections.missed_actions.map((a, i) => (
                  <div key={i} className="text-xs text-slate-200 py-0.5 flex gap-2">
                    <span className="text-red-500">✗</span>{a}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Educational message */}
          <div className="bg-blue-950/40 border border-blue-700 rounded-xl p-4">
            <div className="text-xs font-bold text-blue-300 uppercase tracking-wider mb-2">
              Mensaje educativo
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {debrief.educational_message}
            </p>
          </div>

          {/* Timeline */}
          {sections.timeline.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                Cronología de acciones
              </div>
              <div className="space-y-1">
                {sections.timeline.map((entry, i) => (
                  <div key={i} className="flex items-start gap-3 text-xs border-b border-slate-800/60 pb-1">
                    <span className="font-mono text-cyan-500 w-12 shrink-0 pt-px">
                      {fmtTime(entry.t)}
                    </span>
                    <div className="min-w-0">
                      <span className="text-slate-200">{entry.action}</span>
                      {entry.state_before !== entry.state_after && (
                        <span className="text-yellow-400 ml-2 text-[10px]">→ {entry.state_after}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinical sources */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Fuentes clínicas
            </div>
            <div className="space-y-1">
              {sections.clinical_sources.map((src) => (
                <div key={src.id} className="text-xs text-slate-400">
                  {src.url ? (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline"
                    >
                      {src.title}{src.year ? ` (${src.year})` : ''}
                    </a>
                  ) : (
                    <span>{src.title}{src.year ? ` (${src.year})` : ''}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* PENDING_MEDICAL_REVIEW badge */}
          <div className="bg-yellow-950/40 border border-yellow-700 rounded-xl p-3">
            <p className="text-[10px] font-mono text-yellow-400 text-center">
              {debrief.disclaimer}
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-center pb-4">
            <button
              onClick={onRestart}
              className="bg-blue-700 hover:bg-blue-600 text-white font-semibold px-10 py-3 rounded-xl text-sm transition-colors"
            >
              Reiniciar simulación
            </button>
            <a
              href={api.getPdfUrl(debrief.session_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-slate-700 hover:bg-slate-600 text-white font-semibold px-8 py-3 rounded-xl text-sm transition-colors inline-flex items-center gap-2"
            >
              ⬇ Descargar PDF
            </a>
          </div>

        </div>
      </div>
    </div>
  );
}
