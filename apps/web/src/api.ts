// Thin fetch wrapper for the EARP FastAPI backend.
// In dev, Vite proxies /api/* to http://127.0.0.1:8000/*.
// In prod, Docker writes /config.js from API_BASE_URL at container start.
declare global {
  interface Window {
    __EARP_CONFIG__?: {
      apiBase?: string;
    };
  }
}

const runtimeBase = window.__EARP_CONFIG__?.apiBase?.trim();
const buildBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
const BASE = runtimeBase || buildBase || "/api";

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ReliabilityInput {
  mtbf_hours: number;
  mttr_hours: number;
  mission_time_hours: number;
}

export interface ReliabilityOutput {
  id?: number | null;
  mtbf_hours: number;
  mttr_hours: number;
  mission_time_hours: number;
  availability: number;
  reliability: number;
  failure_rate_per_hour: number;
  expected_failures: number;
  created_at: string;
}

export interface AssessmentInput {
  system_name: string;
  owner: string;
  govern_score: number;
  map_score: number;
  measure_score: number;
  manage_score: number;
  notes?: string;
}

export interface AssessmentOutput extends AssessmentInput {
  id: number;
  overall_score: number;
  risk_tier: "LOW" | "MEDIUM" | "HIGH";
  created_at: string;
  gate_decision?: "allow" | "warn" | "block" | null;
  gate_reasons?: Array<{
    code: string;
    message: string;
    severity: "info" | "warn" | "block";
  }>;
}

export interface AnomalyOutput {
  n_trained_on: number;
  n_scored: number;
  predictions: number[];
  scores: number[];
  anomaly_count: number;
  model: string;
  record_ids?: number[] | null;
}

export interface ReliabilityScoreComponent {
  name: string;
  value: number;
  weight: number;
  nist_function?: "govern" | "map" | "measure" | "manage";
}

export interface ReliabilityScoreInput {
  system_name: string;
  components: ReliabilityScoreComponent[];
}

export interface PolicyGateInput {
  score_input: ReliabilityScoreInput;
}

export interface DashboardMetric {
  key: string;
  label: string;
  value: string;
  target?: string | null;
  status: "good" | "attention" | "blocked" | "empty";
  detail: string;
}

export interface DashboardEpic {
  id: string;
  title: string;
  status: "not_started" | "in_progress" | "done";
  sprint: number;
}

export interface AssessmentSummary {
  total: number;
  low_risk: number;
  medium_risk: number;
  high_risk: number;
  allow_count: number;
  warn_count: number;
  block_count: number;
}

export interface ReliabilityScoreRecord {
  id: number;
  system_name: string;
  composite_score: number;
  tier: string;
  weights_normalized: boolean;
  nist_govern?: number | null;
  nist_map?: number | null;
  nist_measure?: number | null;
  nist_manage?: number | null;
  created_at: string;
}

export interface ReliabilityScoreHistory {
  system_name?: string | null;
  stats: {
    count: number;
    latest_score?: number | null;
    latest_tier?: string | null;
    earliest_score?: number | null;
    earliest_tier?: string | null;
    rolling_average?: number | null;
    min_score?: number | null;
    max_score?: number | null;
    trend_direction: string;
    tier_transitions: Array<{
      from_tier: string;
      to_tier: string;
      at: string;
      composite_score: number;
    }>;
  };
  records: ReliabilityScoreRecord[];
}

export interface PolicyHistoryRecord {
  id: number;
  system_name: string;
  decision: "allow" | "warn" | "block";
  composite_score: number;
  tier: string;
  thresholds: {
    allow_min_composite: number;
    warn_min_composite: number;
    min_nist_function_score: number;
  };
  reasons: Array<{
    code: string;
    message: string;
    severity: "info" | "warn" | "block";
  }>;
  created_at: string;
}

export interface PolicyHistory {
  system_name?: string | null;
  stats: {
    count: number;
    latest_decision?: "allow" | "warn" | "block" | null;
    latest_composite?: number | null;
    earliest_decision?: "allow" | "warn" | "block" | null;
    earliest_composite?: number | null;
    allow_count: number;
    warn_count: number;
    block_count: number;
    allow_rate?: number | null;
    warn_rate?: number | null;
    block_rate?: number | null;
    rolling_average_composite?: number | null;
    min_composite?: number | null;
    max_composite?: number | null;
    trend_direction: string;
    decision_transitions: Array<{
      from_decision: "allow" | "warn" | "block";
      to_decision: "allow" | "warn" | "block";
      at: string;
      composite_score: number;
    }>;
  };
  records: PolicyHistoryRecord[];
}

export interface ComplianceControl {
  control_id: string;
  title: string;
  status: "implemented" | "partial" | "planned" | "blocked";
  summary: string;
  evidence: string[];
  gaps: string[];
}

export interface ComplianceEvidenceBundle {
  generated_at: string;
  overall_status: string;
  controls: ComplianceControl[];
  outstanding_gaps: string[];
  recommended_next_steps: string[];
}

export interface DashboardSummary {
  generated_at: string;
  viewer_role: string;
  release: string;
  branch: string;
  current_sprint: number;
  total_sprints: number;
  epics: DashboardEpic[];
  epic_completion_percent: number;
  metrics: DashboardMetric[];
  assessment_summary: AssessmentSummary;
  recent_assessments: AssessmentOutput[];
  score_history: ReliabilityScoreHistory;
  policy_history: PolicyHistory;
}

export interface ExecutiveSummary {
  generated_at: string;
  viewer_role: string;
  release: string;
  branch: string;
  current_sprint: number;
  total_sprints: number;
  dashboard: DashboardSummary;
  compliance: ComplianceEvidenceBundle;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),

  register: (email: string, password: string) =>
    request<{ id: number; email: string; role: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<Token>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) =>
    request<{ id: number; email: string; role: string }>("/auth/me", {}, token),

  compute: (input: ReliabilityInput) =>
    request<ReliabilityOutput>("/reliability/compute", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  history: () => request<ReliabilityOutput[]>("/reliability/history"),

  createReliabilityScore: (input: ReliabilityScoreInput) =>
    request<Record<string, unknown>>("/reliability/score", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  createAssessment: (token: string, input: AssessmentInput) =>
    request<AssessmentOutput>(
      "/assessments",
      { method: "POST", body: JSON.stringify(input) },
      token
    ),

  listAssessments: (token: string) =>
    request<AssessmentOutput[]>("/assessments", {}, token),

  evaluatePolicy: (input: PolicyGateInput) =>
    request<Record<string, unknown>>("/policy/evaluate", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  getDashboardSummary: (token: string) =>
    request<DashboardSummary>("/dashboard/summary", {}, token),

  getExecutiveSummary: (token: string) =>
    request<ExecutiveSummary>("/reports/executive-summary", {}, token),

  executiveSummaryPdf: async (token: string) => {
    const headers = new Headers();
    headers.set("Authorization", `Bearer ${token}`);
    const res = await fetch(`${BASE}/reports/executive-summary.pdf`, { headers });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${body}`);
    }
    return res.blob();
  },

  anomalyFromHistory: (token: string, contamination = 0.1) =>
    request<AnomalyOutput>(
      `/ai/anomaly-detect/from-history?contamination=${contamination}`,
      {},
      token
    ),
};
