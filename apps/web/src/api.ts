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

  createAssessment: (token: string, input: AssessmentInput) =>
    request<AssessmentOutput>(
      "/assessments",
      { method: "POST", body: JSON.stringify(input) },
      token
    ),

  listAssessments: (token: string) =>
    request<AssessmentOutput[]>("/assessments", {}, token),

  anomalyFromHistory: (token: string, contamination = 0.1) =>
    request<AnomalyOutput>(
      `/ai/anomaly-detect/from-history?contamination=${contamination}`,
      {},
      token
    ),
};
