'use client';
import { useState, useEffect, useCallback } from 'react';
import { Disclaimer } from '@/components/Disclaimer';
import { useAuth } from '@/hooks/useAuth';
import { LoginModal } from '@/components/LoginModal';
import { api } from '@/lib/api';
import type { ValidationRecord } from '@/lib/types';

const SCENARIO_ID = 'anaphylaxis_perioperative_adult_v1';

const PENDING_RULES = [
  { ref: 'action:ADMINISTER_EPINEPHRINE_IM:dose', description: 'Adrenalina IM 0.3 mg — dosis adulto (muslo lateral)' },
  { ref: 'action:ADMINISTER_EPINEPHRINE_IV:dose', description: 'Adrenalina IV 0.1 mg bolo lento — dosis colapso hemodinámico' },
  { ref: 'action:ADMINISTER_EPINEPHRINE_CPR:dose', description: 'Adrenalina 1 mg IV durante RCP según protocolo ACLS' },
  { ref: 'action:ADMINISTER_FLUIDS_IV:dose', description: 'Solución salina 500 mL IV rápido — volumen de expansión' },
  { ref: 'action:ADMINISTER_ANTIHISTAMINE_IV:dose', description: 'Difenhidramina 50 mg IV — dosis antihistamínico' },
  { ref: 'action:ADMINISTER_CORTICOSTEROID:dose', description: 'Metilprednisolona 1 mg/kg IV — dosis corticosteroide' },
  { ref: 'state:INITIAL_PRESENTATION:auto_advance_after_seconds', description: 'Tiempo de presentación inicial antes de signos: 30 s' },
  { ref: 'state:GRADE_I:auto_advance_after_seconds', description: 'Tiempo en Grado I sin tratamiento: 90 s' },
  { ref: 'state:GRADE_II:auto_advance_after_seconds', description: 'Tiempo en Grado II sin tratamiento: 180 s' },
  { ref: 'state:GRADE_III:auto_advance_after_seconds', description: 'Tiempo en Grado III sin tratamiento: 120 s' },
  { ref: 'state:GRADE_IV:auto_advance_after_seconds', description: 'Tiempo en Grado IV (paro) sin RCP: 180 s' },
  { ref: 'vitals:GRADE_I:hr_delta_per_second', description: 'Delta FC Grado I: +0.15 lpm/s' },
  { ref: 'vitals:GRADE_II:sbp_delta_per_second', description: 'Delta PAS Grado II: -0.5 mmHg/s' },
  { ref: 'vitals:GRADE_III:spo2_delta_per_second', description: 'Delta SpO₂ Grado III: -0.35 %/s' },
];

export default function AdminPage() {
  const { user, token, loading, error: authError, login, register, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [validations, setValidations] = useState<ValidationRecord[]>([]);
  const [loadingValidations, setLoadingValidations] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [noteModal, setNoteModal] = useState<{ ref: string; description: string } | null>(null);
  const [noteText, setNoteText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchValidations = useCallback(async () => {
    if (!token) return;
    setLoadingValidations(true);
    try {
      const data = await api.listValidations(SCENARIO_ID);
      setValidations(data);
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : 'Error cargando validaciones');
    } finally {
      setLoadingValidations(false);
    }
  }, [token]);

  useEffect(() => { fetchValidations(); }, [fetchValidations]);

  const validatedRefs = new Set(validations.map((v) => v.rule_ref));

  const handleValidate = async () => {
    if (!noteModal) return;
    setSubmitting(true);
    setApiError(null);
    try {
      await api.createValidation({
        scenario_id: SCENARIO_ID,
        rule_ref: noteModal.ref,
        rule_description: noteModal.description,
        notes: noteText || undefined,
      });
      setNoteModal(null);
      setNoteText('');
      await fetchValidations();
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : 'Error al validar');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    setApiError(null);
    try {
      await api.deleteValidation(id);
      await fetchValidations();
    } catch {
      setApiError('Error al eliminar validación');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        Cargando...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Disclaimer />

      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-slate-200">Panel de Validación Médica</h1>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Escenario: {SCENARIO_ID}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="text-xs text-slate-400">
                {user.full_name}
                {user.role === 'validator' && (
                  <span className="ml-1 text-blue-400 font-semibold">[Validador]</span>
                )}
              </span>
              <button onClick={logout} className="text-xs text-red-400 hover:underline">
                Salir
              </button>
            </>
          ) : (
            <button
              onClick={() => setShowLogin(true)}
              className="text-xs bg-blue-700 hover:bg-blue-600 px-3 py-1.5 rounded-lg text-white font-semibold"
            >
              Iniciar sesión
            </button>
          )}
        </div>
      </div>

      {showLogin && (
        <LoginModal
          onLogin={login}
          onRegister={register}
          onClose={() => setShowLogin(false)}
          error={authError}
        />
      )}

      {!user && (
        <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
          Iniciá sesión para acceder al panel de validación.
        </div>
      )}

      {user && (
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">

            {apiError && (
              <div className="bg-red-950 border border-red-700 rounded-lg px-4 py-2 text-xs text-red-300">
                {apiError}
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold font-mono text-yellow-400">{PENDING_RULES.length}</div>
                <div className="text-[10px] text-slate-500 mt-1">Total a validar</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold font-mono text-green-400">{validations.length}</div>
                <div className="text-[10px] text-slate-500 mt-1">Validadas</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center">
                <div className="text-2xl font-bold font-mono text-red-400">
                  {PENDING_RULES.length - validations.length}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Pendientes</div>
              </div>
            </div>

            {/* Rules list */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Reglas clínicas del escenario
              </div>
              <div className="divide-y divide-slate-800">
                {PENDING_RULES.map((rule) => {
                  const isValidated = validatedRefs.has(rule.ref);
                  const validation = validations.find((v) => v.rule_ref === rule.ref);
                  return (
                    <div key={rule.ref} className="px-4 py-3 flex items-start gap-3">
                      <span className={`mt-0.5 text-sm shrink-0 ${isValidated ? 'text-green-400' : 'text-yellow-400'}`}>
                        {isValidated ? '✓' : '○'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs text-slate-200">{rule.description}</div>
                        <div className="text-[10px] font-mono text-slate-500 mt-0.5">{rule.ref}</div>
                        {isValidated && validation && (
                          <div className="text-[10px] text-green-400 mt-0.5">
                            Validado por {validation.validated_by_name} ·{' '}
                            {new Date(validation.validated_at).toLocaleDateString('es-AR')}
                            {validation.notes && ` · "${validation.notes}"`}
                          </div>
                        )}
                      </div>
                      {user.role === 'validator' && (
                        <div className="shrink-0">
                          {!isValidated ? (
                            <button
                              onClick={() => { setNoteModal(rule); setNoteText(''); }}
                              className="text-[10px] bg-blue-800 hover:bg-blue-700 text-blue-200 px-2 py-1 rounded"
                            >
                              Validar
                            </button>
                          ) : validation && (
                            <button
                              onClick={() => handleDelete(validation.id)}
                              className="text-[10px] text-red-400 hover:underline"
                            >
                              Revocar
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Validated list detail */}
            {validations.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Registro de validaciones
                </div>
                <div className="space-y-2">
                  {validations.map((v) => (
                    <div key={v.id} className="text-xs text-slate-300">
                      <span className="text-green-400">✓</span>{' '}
                      <span className="font-mono text-slate-400">{v.rule_ref}</span>{' '}
                      — {v.validated_by_name} —{' '}
                      {new Date(v.validated_at).toLocaleString('es-AR')}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Note modal */}
      {noteModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          onClick={() => setNoteModal(null)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-xl p-5 w-full max-w-sm mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-sm font-bold text-slate-200 mb-2">Confirmar validación</h3>
            <p className="text-xs text-slate-400 mb-3">{noteModal.description}</p>
            <textarea
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none h-20 focus:outline-none focus:border-blue-500"
              placeholder="Notas opcionales (fuente, versión consultada, observaciones...)"
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setNoteModal(null)}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold py-2 rounded-lg"
              >
                Cancelar
              </button>
              <button
                onClick={handleValidate}
                disabled={submitting}
                className="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-xs font-semibold py-2 rounded-lg"
              >
                {submitting ? 'Guardando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
