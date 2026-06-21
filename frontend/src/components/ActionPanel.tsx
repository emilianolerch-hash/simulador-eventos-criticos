'use client';
import { useState } from 'react';
import type { SessionState, ScenarioDetail } from '@/lib/types';
import { ActionModal } from './ActionModal';

interface Props {
  session: SessionState | null;
  scenario: ScenarioDetail | null;
  onAction: (id: string) => void;
  onAdvanceTime: (s: number) => void;
  loading: boolean;
}

type ModalType = 'medication' | 'procedure' | null;

const BTN_BASE =
  'rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed w-full';

const VARIANTS = {
  green:  `${BTN_BASE} bg-green-700 hover:bg-green-600 text-white`,
  yellow: `${BTN_BASE} bg-yellow-700 hover:bg-yellow-600 text-white`,
  blue:   `${BTN_BASE} bg-blue-700  hover:bg-blue-600  text-white`,
  red:    `${BTN_BASE} bg-red-700   hover:bg-red-600   text-white`,
  purple: `${BTN_BASE} bg-purple-700 hover:bg-purple-600 text-white`,
  cyan:   `${BTN_BASE} bg-cyan-800  hover:bg-cyan-700  text-white`,
  slate:  `${BTN_BASE} bg-slate-700 hover:bg-slate-600 text-white`,
};

function Btn({
  label, variant, enabled, loading, onClick,
}: {
  label: string;
  variant: keyof typeof VARIANTS;
  enabled: boolean;
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={VARIANTS[variant]}
      disabled={!enabled || loading}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function ActionPanel({ session, scenario, onAction, onAdvanceTime, loading }: Props) {
  const [modal, setModal] = useState<ModalType>(null);

  if (!session || !scenario) return null;

  const available = new Set(session.available_actions);
  const acts = scenario.actions;

  const byCategory = (cat: string) =>
    Object.entries(acts).filter(([id, a]) => a.category === cat && available.has(id));

  const canDo = (id: string) => available.has(id);

  const handleSelect = (id: string) => {
    setModal(null);
    onAction(id);
  };

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 space-y-3">
      <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">
        Panel de acciones
      </div>

      {/* Row 1: Communication + Trigger */}
      <div className="grid grid-cols-2 gap-2">
        <Btn
          label="📢 Solicitar ayuda"
          variant="green"
          enabled={canDo('CALL_FOR_HELP')}
          loading={loading}
          onClick={() => onAction('CALL_FOR_HELP')}
        />
        <Btn
          label="🛑 Suspender agente"
          variant="yellow"
          enabled={canDo('STOP_TRIGGER')}
          loading={loading}
          onClick={() => onAction('STOP_TRIGGER')}
        />
      </div>

      {/* Row 2: O2 + Fluids */}
      <div className="grid grid-cols-2 gap-2">
        <Btn
          label="💨 Oxígeno 100%"
          variant="blue"
          enabled={canDo('ADMINISTER_O2_100')}
          loading={loading}
          onClick={() => onAction('ADMINISTER_O2_100')}
        />
        <Btn
          label="💧 Fluidos IV"
          variant="blue"
          enabled={canDo('ADMINISTER_FLUIDS_IV')}
          loading={loading}
          onClick={() => onAction('ADMINISTER_FLUIDS_IV')}
        />
      </div>

      {/* Row 3: Medication + Procedure (open modals) */}
      <div className="grid grid-cols-2 gap-2">
        <Btn
          label="💊 Medicación ▾"
          variant="red"
          enabled={byCategory('medication').length > 0}
          loading={loading}
          onClick={() => setModal('medication')}
        />
        <Btn
          label="🩺 Procedimiento ▾"
          variant="purple"
          enabled={byCategory('procedure').length > 0}
          loading={loading}
          onClick={() => setModal('procedure')}
        />
      </div>

      {/* Row 4: Advance time */}
      <Btn
        label="⏩ Avanzar tiempo  +15 s"
        variant="slate"
        enabled={!session.is_terminal}
        loading={loading}
        onClick={() => onAdvanceTime(15)}
      />

      {/* Effect feedback */}
      {session.effect_summary && (
        <div className="bg-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 border border-slate-700">
          {session.effect_summary}
        </div>
      )}

      {/* Modals */}
      {modal === 'medication' && (
        <ActionModal
          title="Administrar medicación"
          actions={byCategory('medication')}
          onSelect={handleSelect}
          onClose={() => setModal(null)}
        />
      )}
      {modal === 'procedure' && (
        <ActionModal
          title="Realizar procedimiento"
          actions={byCategory('procedure')}
          onSelect={handleSelect}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}
