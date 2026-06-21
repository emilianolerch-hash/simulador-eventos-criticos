export interface VitalSigns {
  hr: number;
  sbp: number;
  dbp: number;
  spo2: number;
  rr: number;
  etco2: number;
  temperature: number;
}

export interface ActionLogEntry {
  entry_id: string;
  sim_time_seconds: number;
  action_id: string;
  action_label: string;
  state_before: string;
  state_after: string;
  effect_summary: string;
}

export interface SessionState {
  session_id: string;
  state: string;
  state_description: string;
  vitals: VitalSigns;
  sim_time_seconds: number;
  is_terminal: boolean;
  outcome_id: string | null;
  available_actions: string[];
  effect_summary?: string;
}

export interface ActionDef {
  label: string;
  description: string;
  category: string | null;
  notes: string | null;
  transitions_to: string | null;
}

export interface ScenarioDetail {
  id: string;
  title: string;
  version: string;
  patient: {
    age: number;
    weight_kg: number;
    sex: string;
    asa_class: string;
    context: string;
  };
  actions: Record<string, ActionDef>;
}

export interface DebriefSource {
  id: string;
  title: string;
  year: number | null;
  url: string | null;
}

export interface DebriefTimeline {
  t: number;
  action: string;
  state_before: string;
  state_after: string;
  summary: string;
}

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  role: 'anesthesiologist' | 'validator';
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface ValidationRecord {
  id: string;
  scenario_id: string;
  rule_ref: string;
  rule_description: string;
  validated_by_name: string;
  validated_at: string;
  notes: string | null;
}

export interface DebriefReport {
  session_id: string;
  outcome_id: string;
  outcome_label: string;
  outcome_description: string;
  educational_message: string;
  total_sim_time_seconds: number;
  total_actions_taken: number;
  sections: {
    correct_actions: string[];
    missed_actions: string[];
    timeline: DebriefTimeline[];
    clinical_sources: DebriefSource[];
  };
  disclaimer: string;
}
