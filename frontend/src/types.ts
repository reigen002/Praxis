export type BusinessRecord = {
  record_id: string; source: string; category: string; title: string; description: string;
  customer_or_team: string; created_at: string; deadline: string | null; status: string;
  owner: string | null; contract_value: string | null; currency: string | null;
  related_record_ids: string[]; severity: string;
}
export type Decision = {
  record_id: string; classification: string; urgency: string; urgency_score: number;
  provider: string; probabilities: Record<string, number> | null; risk_probability: number | null;
  uncertainty: string; error: string | null; fallback: boolean; model_version?: string | null;
  urgency_probabilities?: Record<string, number> | null; team_confidence?: number | null;
  urgency_confidence?: number | null; latency_ms?: number | null; cache_hit?: boolean;
  evaluated_at?: string | null; request_id?: string | null; usage?: Record<string, unknown> | null;
}
export type Metrics = {
  exposure_by_currency: Record<string, string>; pipeline_by_currency: Record<string, string>;
  open_issues: number; overdue_tasks: number; customer_escalations: number;
  opportunities_awaiting_action: number; missing_financial_ids: string[];
  definitions: Record<string, string>; cohorts: Record<string, string[]>; source_ids: string[];
}
export type Event = { timestamp: string; actor: string; kind: string; tool: string | null; source_ids: string[]; detail: string }
export type Priority = {
  rank: number; record_id: string; title: string; category: string; urgency: string;
  business_impact: string; recommended_action: string; suggested_owner: string;
  source_ids: string[]; assumptions: string[];
}
export type FollowUp = { record_id: string; recipient_team: string; draft: string; source_ids: string[]; approval_required: true }
export type RunResult = {
  run_id: string; question: string; model: string; mode: 'live'; elapsed_seconds: number;
  briefing: { executive_summary: string; priorities: Priority[]; follow_ups: FollowUp[]; data_limitations: string[] };
  metrics: Metrics; decisions: Decision[]; events: Event[];
}
export type Overview = {
  dataset: string; label: string; reference_date: string; datasets: { id: string; name: string }[];
  records: BusinessRecord[]; metrics: Metrics; decisions: Decision[];
  profile?: { description: string; comparison_question: string; comparison_label: string;
    exposure_label: string; exposure_note: string; pipeline_label: string;
    opportunities_label: string; escalations_label: string } | null;
  deadlines: { risks: { record_id: string; deadline: string; days_remaining: number; overdue: boolean }[] };
  policy: { escalations: { record_id: string; reason: string; source_ids: string[] }[] };
  readiness: { llm: { configured: boolean; provider: string; model: string };
    jev: { configured: boolean; model: string; live_verified: boolean; cached_record_id: string | null; max_records_per_run: number } };
}
export type Job = { save_warning?: string | null; id: string; status: 'queued' | 'running' | 'completed' | 'failed'; result: RunResult | null; error: string | null; events: Event[] }
export type DecisionComparison = { baseline: Decision; jev: Decision; cached: boolean }
