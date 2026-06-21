'use client';
import type { ActionLogEntry } from '@/lib/types';

function fmtTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

export function Timeline({ log }: { log: ActionLogEntry[] }) {
  const reversed = [...log].reverse();

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col flex-1 min-h-0">
      <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 shrink-0">
        Registro cronológico · {log.length} {log.length === 1 ? 'acción' : 'acciones'}
      </div>
      <div className="overflow-y-auto flex-1 space-y-1 pr-1">
        {reversed.length === 0 ? (
          <div className="text-xs text-slate-600 italic">Sin acciones registradas.</div>
        ) : (
          reversed.map((entry) => (
            <div key={entry.entry_id} className="flex items-start gap-2 text-xs border-b border-slate-800/60 pb-1">
              <span className="font-mono text-cyan-500 w-11 shrink-0 pt-px">
                {fmtTime(entry.sim_time_seconds)}
              </span>
              <div className="min-w-0">
                <span className="text-slate-200 font-medium">{entry.action_label}</span>
                {entry.state_before !== entry.state_after && (
                  <span className="text-yellow-400 ml-1 text-[10px]">
                    → {entry.state_after}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
