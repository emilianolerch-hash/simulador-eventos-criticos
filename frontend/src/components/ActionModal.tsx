'use client';
import type { ActionDef } from '@/lib/types';

interface Props {
  title: string;
  actions: [string, ActionDef][];   // [actionId, ActionDef][]
  onSelect: (id: string) => void;
  onClose: () => void;
}

export function ActionModal({ title, actions, onSelect, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-full max-w-sm mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-200">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-lg leading-none"
          >
            ×
          </button>
        </div>

        {actions.length === 0 ? (
          <p className="text-xs text-slate-500 italic">
            No hay opciones disponibles en este estado.
          </p>
        ) : (
          <div className="space-y-2">
            {actions.map(([id, def]) => (
              <button
                key={id}
                onClick={() => onSelect(id)}
                className="w-full text-left rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-3 transition-colors"
              >
                <div className="text-sm font-semibold text-slate-100">{def.label}</div>
                <div className="text-xs text-slate-400 mt-0.5">{def.description}</div>
                {def.notes && (
                  <div className="text-[10px] text-yellow-400 mt-1 italic">{def.notes}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
