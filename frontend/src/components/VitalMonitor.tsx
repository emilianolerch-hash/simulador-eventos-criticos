'use client';
import type { VitalSigns } from '@/lib/types';

type VitalKey = 'hr' | 'sbp' | 'spo2' | 'rr' | 'etco2';

const RANGES: Record<VitalKey, { green: [number, number]; yellow: [number, number][] }> = {
  hr:    { green: [60, 100],  yellow: [[45, 60], [100, 130]] },
  sbp:   { green: [90, 140],  yellow: [[70, 90], [140, 180]] },
  spo2:  { green: [95, 100],  yellow: [[88, 95]] },
  rr:    { green: [12, 20],   yellow: [[20, 30]] },
  etco2: { green: [35, 45],   yellow: [[25, 35], [45, 55]] },
};

function vitalColor(key: VitalKey, val: number): string {
  const r = RANGES[key];
  if (val >= r.green[0] && val <= r.green[1]) return 'text-green-400';
  for (const [lo, hi] of r.yellow) {
    if (val >= lo && val <= hi) return 'text-yellow-400';
  }
  return 'text-red-500';
}

function fmt(val: number | undefined, dec = 0): string {
  if (val === undefined) return '—';
  return dec > 0 ? val.toFixed(dec) : String(Math.round(val));
}

function fmtTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

function VitalCell({
  label, value, unit, colorKey, large = false,
}: {
  label: string;
  value: number | undefined;
  unit: string;
  colorKey?: VitalKey;
  large?: boolean;
}) {
  const color = value !== undefined && colorKey ? vitalColor(colorKey, value) : 'text-slate-300';
  const size = large ? 'text-5xl' : 'text-4xl';
  return (
    <div className="bg-slate-900 rounded-lg p-3 flex flex-col items-center border border-slate-800">
      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">{label}</span>
      <span className={`${size} font-mono font-bold ${color} leading-none`}>{fmt(value)}</span>
      <span className="text-[10px] text-slate-500 mt-1">{unit}</span>
    </div>
  );
}

export function VitalMonitor({
  vitals,
  simTime,
}: {
  vitals: VitalSigns | undefined;
  simTime: number;
}) {
  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
          Monitor de signos vitales
        </span>
        <span className="text-sm font-mono text-cyan-400 font-bold">
          ⏱ {fmtTime(simTime)}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <VitalCell label="FC" value={vitals?.hr} unit="lpm" colorKey="hr" large />
        <div className="bg-slate-900 rounded-lg p-3 flex flex-col items-center border border-slate-800 col-span-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">PA</span>
          <span className={`text-3xl font-mono font-bold leading-none ${vitals?.sbp !== undefined ? vitalColor('sbp', vitals.sbp) : 'text-slate-300'}`}>
            {fmt(vitals?.sbp)}<span className="text-xl text-slate-500">/{fmt(vitals?.dbp)}</span>
          </span>
          <span className="text-[10px] text-slate-500 mt-1">mmHg</span>
        </div>
        <VitalCell label="SpO₂" value={vitals?.spo2} unit="%" colorKey="spo2" large />
        <VitalCell label="FR" value={vitals?.rr} unit="rpm" colorKey="rr" />
        <VitalCell label="EtCO₂" value={vitals?.etco2} unit="mmHg" colorKey="etco2" />
        <VitalCell label="Temp" value={vitals?.temperature} unit="°C" />
      </div>
    </div>
  );
}
