export const API_URL = "/api";

export type Step = {
  step: string;
  status: "queued" | "running" | "done" | "error";
  error: string | null;
  result: Record<string, unknown> | null;
};

export type Check = { id: string; result: string; detail: string };

export type Verdict = {
  verdict: "PASSED" | "FAILED" | "INCONCLUSIVE";
  reasons: string[];
  checks: Check[];
  conditions: { supply: string | null; head_cm: number | null; water_level_cm: number | null };
  run_s: number | null;
  uncertainties: string[];
  requested_actions: string[];
  thresholds_version: string | null;
};

export type Job = {
  id: string;
  token: string;
  data_class: string;
  state: string;
  fault: string | null;
  steps: Step[];
  verdict: Verdict | null;
  evidence: string[];
  record: { verdict: string; review: string | null; note: string } | null;
};

export type Triage = {
  causes: { fault_id: string; likelihood: number; evidence: string[] }[];
  requested_check: { instruction: string; component_concept: string };
  transcript?: string;
};

export type Guidance = {
  stop_conditions: string[];
  steps: { text: string; component_concept: string; requires_approval: boolean }[];
  cited_sections: string[];
};

export type ServiceRecord = {
  job_id: string;
  job_token: string;
  data_class: string;
  equipment: string;
  fault_hypothesis: string;
  symptom_transcript: string;
  verdict: Verdict["verdict"];
  reasons: string[];
  checks: Check[];
  measurements: {
    fill_time_video_s: number | null;
    fill_time_typed_s: number | null;
    run_s: number | null;
  };
  conditions: Verdict["conditions"];
  uncertainties: string[];
  requested_actions: string[];
  evidence_frames: string[];
  guide_sections: string[];
  models: Record<string, string>;
  thresholds_version: string | null;
  created_at: string;
  verified_at: string;
  review: { decision: string | null; note: string; reviewed_at: string | null };
};

export type Call = {
  ts: string;
  component: string;
  model: string;
  latency_ms: number | null;
  cost_usd: number;
  cached: boolean;
};

export type Trace = {
  steps: {
    step: string;
    status: string;
    error: string | null;
    calls: Call[];
    latency_ms: number;
    cost_usd: number;
  }[];
  total_calls: number;
  total_cost_usd: number;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return body as T;
}

export function postJson<T>(path: string, data: unknown): Promise<T> {
  return api<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function uploadMedia(jobId: string, kind: string, file: File) {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  return api<{ state: string }>(`/jobs/${jobId}/media`, { method: "POST", body: form });
}
