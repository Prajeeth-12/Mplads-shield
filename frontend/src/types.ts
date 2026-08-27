export interface AlertBrief {
  alert_id: string
  project_id: string
  work_name: string
  severity: string
  headline: string
  score: number
}

export interface StateRisk {
  state: string
  total: number
  high_risk_share: number
}

export interface OverviewData {
  total_projects: number
  total_sanctioned: number
  total_spent: number
  tier_counts: {
    LOW: number
    MEDIUM: number
    HIGH: number
    CRITICAL: number
  }
  critical_alerts: AlertBrief[]
  state_risk: StateRisk[]
  indicator_frequency: { indicator: string; count: number }[]
}

export interface ProjectListItem {
  project_id: string
  work_name: string
  district: string
  category: string
  sanctioned_amount: number
  total_expenditure: number
  progress_pct: number
  score: number
  tier: string
  top_reason: string | null
}

export interface ProjectListResponse {
  total: number
  page: number
  size: number
  items: ProjectListItem[]
}

export interface ScoreDetail {
  total: number
  tier: string
  rank: number
  financial: number
  progress: number
  payment: number
  duplication: number
  temporal: number
  compliance: number
}

export interface EvidenceItem {
  code: string
  dimension: string
  points: number
  headline: string
  detail: string
  features: Record<string, number | string>
  peer_context: Record<string, unknown>
  confidence: string
}

export interface TransactionItem {
  txn_id: string
  txn_date: string
  amount: number
  txn_type: string
  milestone_progress_at_payment: number
}

export interface ProgressItem {
  update_date: string
  progress_pct: number
}

export interface DuplicateItem {
  project_id: string
  work_name: string
  similarity: number
  day_gap: number
  cost_ratio: number
  same_agency: boolean
}

export interface HistoryItem {
  snapshot_date: string
  total_score: number
}

export interface ExplanationDetail {
  summary: string
  reasons: string[]
  action: string
  confidence: string
}

export interface ProjectDetail {
  project: {
    project_id: string
    work_name: string
    description: string
    category: string
    state: string
    district: string
    constituency: string
    mp_name: string
    agency_id: string
    sanctioned_amount: number
    sanction_date: string
    expected_completion: string
    actual_completion: string | null
    status: string
    lat: number
    lon: number
    has_completion_cert: number
    data_source: string
    fiscal_year: string
  }
  financials: TransactionItem[]
  progress: ProgressItem[]
  score: ScoreDetail
  evidence: EvidenceItem[]
  duplicates: DuplicateItem[]
  history: HistoryItem[]
  explanation: ExplanationDetail
}

export interface AlertItem {
  alert_id: string
  project_id: string
  work_name: string
  severity: string
  headline: string
  recommended_action: string
  score: number
  created_at: string
  status: string
}

export interface CategoryAnomaly {
  category: string
  total: number
  high_risk_pct: number
}

export interface IndicatorFrequency {
  indicator: string
  label: string
  count: number
}

export interface AnalyticsData {
  state_risk: (StateRisk & { high_count: number; critical_count: number })[]
  category_anomaly_rate: CategoryAnomaly[]
  scatter: { project_id: string; utilisation_pct: number; progress_pct: number; tier: string }[]
  indicator_frequency: IndicatorFrequency[]
}
