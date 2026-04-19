const BASE = "/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export interface GateDecision {
  decision_id: string;
  evaluation_id: string;
  policy_score: number;
  result: "pass" | "conditional" | "fail";
  rationale: string | null;
  decided_at: string;
}

export interface AuditReport {
  decision_id: string;
  evaluation_id: string;
  policy_score: number;
  result: string;
  rationale: string | null;
  decided_at: string;
  model_id: string;
  model_version: string;
  prompt_set_id: string;
  prompt_set_version: string;
  generated_at: string;
  report_uri: string;
}

export const api = {
  getAuditReport: (decisionId: string) =>
    request<AuditReport>(`/reports/audit/${decisionId}`),
};
